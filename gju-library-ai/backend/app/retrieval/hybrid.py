from sqlalchemy.orm import Session

from app.config import get_settings

from .databases import match_databases
from .fusion import reciprocal_rank_fusion
from .interface import RetrievalResult
from .lexical import lexical_search
from .reranker import rerank
from .routing import RuleBasedRouter
from .semantic import semantic_search


class HybridRetriever:
    def __init__(self, db: Session, router=None):
        self.db = db
        self.router = router or RuleBasedRouter()
        self.s = get_settings()

    def search(
        self, query: str, lang: str | None = None, k: int | None = None
    ) -> RetrievalResult:
        s = self.s
        route = self.router.route(query)
        lang = lang or route.lang
        k = k or s.final_topk

        lex = lexical_search(self.db, query, k=s.retrieve_topk_lexical)
        sem = semantic_search(
            self.db, query, k=s.retrieve_topk_semantic, model_name=s.embedding_model
        )
        fused = reciprocal_rank_fusion([lex, sem], k=s.rrf_k, top=s.rerank_topk)
        ranked = rerank(query, fused, top=k, model_name=s.reranker_model)
        databases = match_databases(
            self.db,
            query_subjects=route.subjects,
            passages=ranked,
            lang=lang,
            max_results=s.db_suggestions_max,
        )
        return RetrievalResult(
            passages=ranked,
            databases=databases,
            debug={
                "lang": lang,
                "subjects": route.subjects,
                "n_lex": len(lex),
                "n_sem": len(sem),
                "n_fused": len(fused),
            },
        )
