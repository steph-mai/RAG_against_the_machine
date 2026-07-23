import fire
from functools import wraps
from pathlib import Path
from src.models import StudentSearchResults, StudentSearchResultsAndAnswer
from src.utils.logger import logger
from src.errors import RagCliArgumentError, RagError
from src.codebase_indexer.indexer import DocIndexer


def handle_cli_errors(function) -> callable:
    @wraps(function)
    # permet de conserver les métadonnées de la function
    def wrapper(*args, **kwargs):
        # création d'un "garde du corps qui accepte toutes les fonctions
        try:
            return function(*args, **kwargs)
        # demande à  la fonction de s'exécuter
        except RagError as e:
            logger.error(e)
        except Exception as e:
            logger.error(f"[CRITICAL ERROR] Unexpected error: {e}")
        # c'est lui qui récupère les erreurs.
    return wrapper
    # on renvoie un garde du corps prêt à agir.


class RAGCli():
    @handle_cli_errors
    def index(self, max_chunk_size: int = 2000) -> Path:
        # Ingest data/raw/ and build the index under data/processed/.
        if max_chunk_size <= 0:
            raise RagCliArgumentError(
                "max_chunk_size must be a positive integer.")
        # gerer le déroulé de l'indexation avec tqdm dans la classe Indexer
        indexer = DocIndexer(max_chunk_size=2000)
        index_path: Path = indexer.build_and_save_index()
        return index_path

        # pour afficher le contenu des chunks en test
        # indexer = DocIndexer()
        # chunks = indexer.build_and_save_index()
        # total_chunks = len(chunks)

        # print(f"✅ Ingestion complete! Indexed {total_chunks} chunks under data/processed/")

        # # ==========================================
        # # 2. AFFICHAGE DE L'ÉCHANTILLON (Les 3 premiers)
        # # ==========================================
        # print("\n" + "="*60)
        # print("🔍 ÉCHANTILLON DES 3 PREMIERS CHUNKS")
        # print("="*60)

        # # On boucle uniquement sur les 3 premiers éléments (chunks[:3])
        # for i, source in enumerate(chunks[:3], 1):
        #     # Comme MinimalSource ne contient que les index, il faut rouvrir le fichier
        #     with open(source.file_path, "r", encoding="utf-8") as f:
        #         full_content = f.read()

        #     # On découpe exactement le texte du chunk avec les index
        #     chunk_text = full_content[source.first_character_index : source.last_character_index]

        #     print(f"\n📦 CHUNK N°{i}/{total_chunks} | Fichier : {source.file_path}")
        #     print(f"   Index : [{source.first_character_index} -> {source.last_character_index}]")
        #     print(f"   Taille : {len(chunk_text)} caractères")
        #     print("." * 40)

        #     # On affiche un aperçu (les 5 premières lignes max)
        #     lines = chunk_text.splitlines()
        #     for line in lines[:5]:
        #         print(f"   | {line}")

        #     if len(lines) > 5:
        #         print("   | [... reste du contenu masqué ...]")
        #     print("." * 40)

    @handle_cli_errors
    def search(self, query: str, k: int):
        # Return the top-k sources for a single query.
        if not query:
            raise RagCliArgumentError("There is no query.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")
        return query

    @handle_cli_errors
    def search_dataset(
            self, dataset_path: str, k: int, save_directory: str
            ) -> StudentSearchResults:
        # Run search over a whole dataset and write a
        # StudentSearchResults JSON file.
        if not dataset_path:
            raise RagCliArgumentError("Give a valid dataset_path.")
        if not save_directory:
            raise RagCliArgumentError("Give a valid save_directory.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")
        return save_directory

    @handle_cli_errors
    def answer(self, query: str, k: int):
        # Answer a single query using the retrieved context.
        if not query:
            raise RagCliArgumentError("There is no query.")
        if k <= 0:
            raise RagCliArgumentError("k must be a positive integer.")
        return k

    @handle_cli_errors
    def answer_dataset(
            self, student_search_results_path: str, save_directory: str
            ) -> StudentSearchResultsAndAnswer:
        # Generate answers for a dataset, producing a
        # StudentSearchResultsAndAnswer JSON file.
        if not student_search_results_path:
            raise RagCliArgumentError(
                "Give a valid student_search_results_path.")
        if not save_directory:
            raise RagCliArgumentError("Give a valid save_directory.")
        return save_directory

    @handle_cli_errors
    def evaluate(self, student_search_results_path: str, dataset_path: str):
        # Report your own recall@k against a ground-truth dataset,
        # for your own testing
        if not student_search_results_path:
            raise RagCliArgumentError(
                "Give a valid student_search_results_path.")
        if not dataset_path:
            raise RagCliArgumentError("Give a valid dataset_path.")
        return dataset_path


if __name__ == "__main__":
    fire.Fire(RAGCli)
