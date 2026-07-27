import json
from pathlib import Path
from src.errors import RagLoadError, RagValidationError
from src.dataset_loader import Dataset_loader
from src.models import StudentSearchResults

class Evaluator:
    def run(self, student_search_results_path: str, dataset_path: str) -> float:
        loader = Dataset_loader()
        ground_truth_dataset = loader.dataset_load(dataset_path)

        # 2. Chargement des résultats de l'étudiant
        student_path = Path(student_search_results_path)
        if not student_path.exists():
            raise RagLoadError(f"File not found: {student_search_results_path}")

        try:
            with open(student_path, mode="r", encoding="utf-8") as f:
                student_data = json.load(f)
            # Validation Pydantic de tes résultats !
            student_results = StudentSearchResults(**student_data)
        except json.JSONDecodeError as e:
            raise RagLoadError(f"Invalid JSON in {student_path.name}: {e}")
        except Exception as e:
            raise RagValidationError(student_path.name, e)

        # 3. Cartographie des sources attendues (Ground Truth) par question_id
        # On utilise un 'set' (ensemble) de file_paths pour faciliter l'intersection mathématique
        gt_sources_map = {}
        for q in ground_truth_dataset.rag_questions:
            # On s'assure que c'est bien une AnsweredQuestion (qui possède l'attribut sources)
            if hasattr(q, "sources"):
                gt_sources_map[q.question_id] = {src.file_path for src in q.sources}

        if not gt_sources_map:
            print("Aucune question répondue (avec sources) n'a été trouvée dans le dataset de référence.")
            return 0.0

        # 4. Calcul du Recall@k pour chaque question
        total_recall = 0.0
        queries_evaluated = 0

        for search_result in student_results.search_results:
            q_id = search_result.question_id

            # Si on n'a pas la vérité absolue pour cette question, on l'ignore
            if q_id not in gt_sources_map:
                continue

            gt_paths = gt_sources_map[q_id]
            if not gt_paths:
                continue # Ignore si la vérité absolue est vide

            # Les chemins de fichiers trouvés par ton algorithme
            retrieved_paths = {src.file_path for src in search_result.retrieved_sources}

            # Application de la formule : Intersection / Total attendu
            intersection = gt_paths.intersection(retrieved_paths)
            recall = len(intersection) / len(gt_paths)

            total_recall += recall
            queries_evaluated += 1

        if queries_evaluated == 0:
            return 0.0

        # 5. Calcul de la moyenne globale
        average_recall = total_recall / queries_evaluated
        k_value = student_results.k

        print(f"\nÉvaluation terminée sur {queries_evaluated} requêtes.")
        print(f"** Moyenne Recall@{k_value} : {average_recall * 100:.2f}% **\n")

        return average_recall
