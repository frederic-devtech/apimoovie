from fastapi import FastAPI, HTTPException, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional   
from database import SessionLocal
import query_helpers as helpers
import schemas

api_description = """
ienvenue dans l'API MovieLens

Cette API permet d'interagir avec une base de données inspirée du célèbre jeu de données [MovieLens](https://grouplens.org/datasets/movielens/).  
Elle est idéale pour découvrir comment consommer une API REST avec des données de films, d'utilisateurs, d'évaluations, de tags et de liens externes (IMDB, TMDB).

### Fonctionnalités disponibles :

- Rechercher un film par ID, ou lister tous les films
- Consulter les évaluations (ratings) par utilisateur et/ou film
- Accéder aux tags appliqués par les utilisateurs sur les films
- Obtenir les liens IMDB / TMDB pour un film
- Voir des statistiques globales sur la base

Tous les endpoints supportent la pagination (`skip`, `limit`) et des filtres optionnels selon les cas.

### Bon à savoir
- Vous pouvez tester tous les endpoints directement via l'interface Swagger "/docs".
- Pour toute erreur (ex : ID inexistant), une réponse claire est retournée avec le bon code HTTP.
 """

# --- Initialisation de l'application FastAPI ---   
app = FastAPI(
    title="MovieLens API", 
    description=api_description, 
    version="1.0"
)


# --- Dépendance pour obtenir une session de base de données ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Endpoint pour tester la santé de l'API ---
@app.get(
    "/",
    tags=["monitoring"],
    summary="Vérifie la santé de l'API",
    description="Un endpoint simple pour vérifier que l'API est opérationnelle.",
    response_description="Message de succès indiquant que l'API est en bonne santé.",
    operation_id="check_health"
)

async def root():
    return {"message": "API MovieLens est opérationnelle!"}


# Endpoint pour récupérer un film par son ID
@app.get(
    "/movies/{movie_id}", # /movies/1
    response_model=schemas.MovieDetailed,
    tags=["films"],
    summary="Récupère les détails d'un film par son ID",
    description="Récupère les détails d'un film, y compris les évaluations, les tags et les liens associés, en utilisant l'ID du film.",
    response_description="Détails du film, y compris les évaluations, les tags et les liens associés.",
    operation_id="get_movie_by_id"
)   
def read_movie(
    movie_id: int = Path(..., description="L'ID du film à récupérer"), 
    db: Session = Depends(get_db)
):
    movie = helpers.get_movie(db, movie_id)
    if movie is None: 
        raise HTTPException(status_code=404, detail=f"Film avec l'ID {movie_id} non trouvé") 
    return movie


# Endpoint pour récupérer une liste de films (avec pagination et filtres facultatifs)
@app.get(
    "/movies", 
    response_model=List[schemas.MovieSimple], 
    tags=["films"], 
    summary="Récupère une liste de films avec pagination et filtres", 
    description="Récupère une liste de films avec des options de pagination et de filtrage par titre et genre.", 
    response_description="Une liste de films correspondant aux critères de recherche.", 
    operation_id="get_movies_list" 
)
def list_movies( 
    skip: int = Query(0, ge=0, description="Nombre de films à ignorer pour la pagination"), 
    limit: int = Query(100, le=1000, description="Nombre maximum de films à retourner"), 
    title: Optional[str] = Query(None, description="Filtrer les films par titre (recherche partielle)"), 
    genre: Optional[str] = Query(None, description="Filtrer les films par genre (recherche partielle)"), 
    db: Session = Depends(get_db) 
): 
    movies = helpers.get_movies(db, skip=skip, limit=limit, title=title, genre=genre)
    return movies

# Endpoint pour obtenir une évaluation par utilisateur et film
@app.get(
    "/ratings/{user_id}/{movie_id}",
    response_model=schemas.RatingSimple,
    tags=["évaluations"],
    summary="Récupère une évaluation par utilisateur et film",
    description="Récupère une évaluation spécifique en fonction de l'ID utilisateur et de l'ID du film.",
    response_description="Détails de l'évaluation pour le couple (userId, movieId).",
    operation_id="get_rating_by_user_and_movie"
)
def read_rating(
    user_id: int = Path(..., description="L'ID de l'utilisateur"), 
    movie_id: int = Path(..., description="L'ID du film"), 
    db: Session = Depends(get_db)
):
    rating = helpers.get_rating(db, user_id, movie_id)
    if rating is None: 
        raise HTTPException(status_code=404, detail=f"Évaluation pour userId {user_id} et movieId {movie_id} non trouvée") 
    return rating

# Endpoint pour obtenir une liste d'évaluations avec filtres
@app.get( 
    "/ratings", 
    response_model=List[schemas.RatingSimple], 
    tags=["évaluations"], 
    summary="Récupère une liste d'évaluations avec filtres", 
    description="Récupère une liste d'évaluations avec des options de pagination et de filtrage par ID de film, ID d'utilisateur et note minimale.", 
    response_description="Une liste d'évaluations correspondant aux critères de recherche.", 
    operation_id="get_ratings_list" 
)
def list_ratings(
    skip: int = Query(0, ge=0, description="Nombre d'évaluations à ignorer pour la pagination"), 
    limit: int = Query(100, le=1000, description="Nombre maximum d'évaluations à retourner"), 
    movie_id: Optional[int] = Query(None, description="Filtrer les évaluations par ID de film"), 
    user_id: Optional[int] = Query(None, description="Filtrer les évaluations par ID d'utilisateur"), 
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Filtrer les évaluations par note minimale (entre 0.0 et 5.0)"), 
    db: Session = Depends(get_db) 
): 
    ratings = helpers.get_ratings(db, skip=skip, limit=limit, movie_id=movie_id, user_id=user_id, min_rating=min_rating)
    return ratings

# Endpoint pour retourner un tag pour un utilisateur et un film donnés, avec le texte du tag
@app.get(
    "/tags/{user_id}/{movie_id}/{tag_text}",
    summary="Obtenir un tag spécifique",
    description="Retourne un tag pour un utilisateur et un film donnés, avec le texte du tag.",
    response_model=schemas.TagSimple,
    tags=["tags"],
)
def read_tag(
    user_id: int = Path(..., description="ID de l'utilisateur"),
    movie_id: int = Path(..., description="ID du film"),
    tag_text: str = Path(..., description="Contenu exact du tag"),
    db: Session = Depends(get_db)
):
    result = helpers.get_tag(db, user_id=user_id, movie_id=movie_id, tag_text=tag_text)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tag non trouvé pour l'utilisateur {user_id}, le film {movie_id} et le tag '{tag_text}'"
        )
    return result


# Endpoint pour retourner une liste de tags avec pagination et filtres facultatifs par utilisateur ou film
@app.get(
    "/tags",
    summary="Lister les tags",
    description="Retourne une liste de tags avec pagination et filtres facultatifs par utilisateur ou film.",
    response_model=List[schemas.TagSimple],
    tags=["tags"],
)
def list_tags(
    skip: int = Query(0, ge=0, description="Nombre de résultats à ignorer"),
    limit: int = Query(100, le=1000, description="Nombre maximal de résultats à retourner"),
    movie_id: Optional[int] = Query(None, description="Filtrer par ID de film"),
    user_id: Optional[int] = Query(None, description="Filtrer par ID d'utilisateur"),
    db: Session = Depends(get_db)
):
    return helpers.get_tags(db, skip=skip, limit=limit, movie_id=movie_id, user_id=user_id)


# Endpoint pour retourner les identifiants IMDB et TMDB pour un film donné
@app.get(
    "/links/{movie_id}",
    summary="Obtenir le lien d'un film",
    description="Retourne les identifiants IMDB et TMDB pour un film donné.",
    response_model=schemas.LinkSimple,
    tags=["links"],
)
def read_link(
    movie_id: int = Path(..., description="ID du film"),
    db: Session = Depends(get_db)
):
    result = helpers.get_link(db, movie_id=movie_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun lien trouvé pour le film avec l'ID {movie_id}"
        )
    return result


# Endpoint pour retourner une liste paginée des identifiants IMDB et TMDB de tous les films
@app.get(
    "/links",
    summary="Lister les liens des films",
    description="Retourne une liste paginée des identifiants IMDB et TMDB de tous les films.",
    response_model=List[schemas.LinkSimple],
    tags=["links"],
)
def list_links(
    skip: int = Query(0, ge=0, description="Nombre de résultats à ignorer"),
    limit: int = Query(100, le=1000, description="Nombre maximal de résultats à retourner"),
    db: Session = Depends(get_db)
):
    return helpers.get_links(db, skip=skip, limit=limit)


# Endpoint pour obtenir des statistiques sur la base de données
@app.get(
    "/analytics",
    summary="Obtenir des statistiques",
    description="""
    Retourne un résumé analytique de la base de données :

    - Nombre total de films
    - Nombre total d’évaluations
    - Nombre total de tags
    - Nombre de liens vers IMDB/TMDB
    """,
    response_model=schemas.AnalyticsResponse,
    tags=["analytics"]
)
def get_analytics(db: Session = Depends(get_db)):
    movie_count = helpers.get_movie_count(db)
    rating_count = helpers.get_rating_count(db)
    tag_count = helpers.get_tag_count(db)
    link_count = helpers.get_link_count(db)

    return schemas.AnalyticsResponse(
        movie_count=movie_count,
        rating_count=rating_count,
        tag_count=tag_count,
        link_count=link_count
    )