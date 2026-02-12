"""API FastAPI pour la gestion de films"""
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

# Imports locaux
from database import SessionLocal, engine, Base
from models import Movie, Rating, Tag, Link
from schemas import (
    MovieBase, MovieDetailed, MovieSimple, 
    RatingBase, RatingSimple, 
    TagBase, TagSimple, 
    LinkBase, LinkSimple
)
import query_helpers as qh

# Création des tables
Base.metadata.create_all(bind=engine)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="API Movies",
    description="API pour gérer une base de données de films avec notes, tags et liens",
    version="1.0.0"
)


# ==================== DEPENDENCY ====================

def get_db():
    """
    Dépendance pour obtenir une session de base de données.
    La session est automatiquement fermée après chaque requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== ROUTES PRINCIPALES ====================

@app.get("/", tags=["Accueil"])
def home():
    """Page d'accueil de l'API avec les endpoints disponibles"""
    return {
        "message": "Bienvenue sur l'API Movies",
        "endpoints": {
            "movies": "/movies - Liste tous les films",
            "movie_detail": "/movies/{movie_id} - Détails d'un film",
            "search": "/movies/search - Recherche de films",
            "top_rated": "/movies/top - Films les mieux notés",
            "most_rated": "/movies/popular - Films les plus notés",
            "statistics": "/statistics - Statistiques générales",
            "docs": "/docs - Documentation interactive"
        }
    }


@app.get("/statistics", tags=["Statistiques"])
def get_statistics(db: Session = Depends(get_db)):
    """
    Obtenir des statistiques générales sur la base de données.
    Retourne le nombre total de films, notes, tags, utilisateurs et la note moyenne.
    """
    stats = qh.get_statistics(db)
    return stats


# ==================== ROUTES MOVIES ====================

@app.get("/movies", response_model=List[MovieSimple], tags=["Movies"])
def get_movies(
    skip: int = Query(0, ge=0, description="Nombre de résultats à sauter"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste de tous les films avec pagination.
    
    - **skip**: Pagination - nombre de résultats à sauter
    - **limit**: Nombre maximum de résultats (max 500)
    """
    movies = qh.get_all_movies(db, skip=skip, limit=limit)
    return movies


@app.get("/movies/{movie_id}", tags=["Movies"])
def get_movie_details(movie_id: int, db: Session = Depends(get_db)):
    """
    Récupérer tous les détails d'un film spécifique.
    Inclut le film, sa note moyenne, le nombre de notes, les tags et les liens.
    
    - **movie_id**: ID du film à rechercher
    """
    details = qh.get_movie_details(db, movie_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Film {movie_id} non trouvé")
    return details


@app.get("/movies/search/by-title", response_model=List[MovieSimple], tags=["Movies"])
def search_by_title(
    title: str = Query(..., min_length=1, description="Titre ou partie du titre à rechercher"),
    db: Session = Depends(get_db)
):
    """
    Rechercher des films par titre (recherche partielle).
    
    - **title**: Texte à rechercher dans le titre
    """
    movies = qh.get_movies_by_title(db, title)
    if not movies:
        raise HTTPException(status_code=404, detail=f"Aucun film trouvé avec le titre '{title}'")
    return movies


@app.get("/movies/search/by-genre", response_model=List[MovieSimple], tags=["Movies"])
def search_by_genre(
    genre: str = Query(..., description="Genre à rechercher (ex: Action, Comedy)"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les films d'un genre spécifique.
    
    - **genre**: Genre à rechercher (ex: "Action", "Comedy", "Drama")
    """
    movies = qh.get_movies_by_genre(db, genre)
    if not movies:
        raise HTTPException(status_code=404, detail=f"Aucun film trouvé pour le genre '{genre}'")
    return movies


@app.get("/movies/search/by-year", response_model=List[MovieSimple], tags=["Movies"])
def search_by_year(
    year: int = Query(..., ge=1800, le=2100, description="Année de sortie"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les films d'une année spécifique.
    
    - **year**: Année de sortie du film
    """
    movies = qh.get_movies_by_year(db, year)
    if not movies:
        raise HTTPException(status_code=404, detail=f"Aucun film trouvé pour l'année {year}")
    return movies


@app.get("/movies/search/advanced", tags=["Movies"])
def advanced_search(
    title: Optional[str] = Query(None, description="Titre à rechercher"),
    genre: Optional[str] = Query(None, description="Genre à rechercher"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Note minimum"),
    min_rating_count: Optional[int] = Query(None, ge=1, description="Nombre minimum de notes"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """
    Recherche avancée avec filtres multiples combinables.
    
    - **title**: Recherche partielle dans le titre
    - **genre**: Genre à rechercher
    - **min_rating**: Note moyenne minimale requise
    - **min_rating_count**: Nombre minimum de notes requises
    - **limit**: Nombre maximum de résultats
    """
    results = qh.search_movies(
        db, 
        title=title, 
        genre=genre, 
        min_rating=min_rating,
        min_rating_count=min_rating_count,
        limit=limit
    )
    if not results:
        raise HTTPException(status_code=404, detail="Aucun film ne correspond à ces critères")
    return results


@app.get("/movies/{movie_id}/similar", response_model=List[MovieSimple], tags=["Movies"])
def get_similar_movies(
    movie_id: int,
    limit: int = Query(10, ge=1, le=50, description="Nombre de films similaires"),
    db: Session = Depends(get_db)
):
    """
    Trouver des films similaires basés sur les genres communs.
    
    - **movie_id**: ID du film de référence
    - **limit**: Nombre de films similaires à retourner
    """
    similar = qh.get_similar_movies(db, movie_id, limit)
    if not similar:
        raise HTTPException(status_code=404, detail=f"Aucun film similaire trouvé pour le film {movie_id}")
    return similar


@app.get("/movies/top/rated", tags=["Movies"])
def get_top_rated(
    min_ratings: int = Query(10, ge=1, description="Nombre minimum de notes requises"),
    limit: int = Query(10, ge=1, le=100, description="Nombre de films à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les films les mieux notés.
    Filtre les films avec un minimum de notes pour éviter les biais.
    
    - **min_ratings**: Nombre minimum de notes requises
    - **limit**: Nombre de films à retourner
    """
    top_movies = qh.get_top_rated_movies(db, min_ratings, limit)
    return top_movies


@app.get("/movies/top/popular", tags=["Movies"])
def get_most_popular(
    limit: int = Query(10, ge=1, le=100, description="Nombre de films à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les films les plus populaires (les plus notés).
    
    - **limit**: Nombre de films à retourner
    """
    popular_movies = qh.get_most_rated_movies(db, limit)
    return popular_movies


# ==================== ROUTES RATINGS ====================

@app.get("/movies/{movie_id}/ratings", response_model=List[RatingSimple], tags=["Ratings"])
def get_movie_ratings(movie_id: int, db: Session = Depends(get_db)):
    """
    Récupérer toutes les notes d'un film spécifique.
    
    - **movie_id**: ID du film
    """
    ratings = qh.get_movie_ratings(db, movie_id)
    if not ratings:
        raise HTTPException(status_code=404, detail=f"Aucune note trouvée pour le film {movie_id}")
    return ratings


@app.get("/movies/{movie_id}/ratings/average", tags=["Ratings"])
def get_average_rating(movie_id: int, db: Session = Depends(get_db)):
    """
    Obtenir la note moyenne d'un film.
    
    - **movie_id**: ID du film
    """
    avg_rating = qh.get_movie_average_rating(db, movie_id)
    if avg_rating is None:
        raise HTTPException(status_code=404, detail=f"Aucune note trouvée pour le film {movie_id}")
    
    rating_count = qh.get_movie_rating_count(db, movie_id)
    return {
        "movie_id": movie_id,
        "average_rating": avg_rating,
        "rating_count": rating_count
    }


@app.get("/users/{user_id}/ratings", response_model=List[RatingSimple], tags=["Ratings"])
def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    """
    Récupérer toutes les notes d'un utilisateur.
    
    - **user_id**: ID de l'utilisateur
    """
    ratings = qh.get_user_ratings(db, user_id)
    if not ratings:
        raise HTTPException(status_code=404, detail=f"Aucune note trouvée pour l'utilisateur {user_id}")
    return ratings


@app.get("/users/{user_id}/recommendations", tags=["Ratings"])
def get_recommendations(
    user_id: int,
    limit: int = Query(10, ge=1, le=50, description="Nombre de recommandations"),
    db: Session = Depends(get_db)
):
    """
    Obtenir des recommandations personnalisées pour un utilisateur.
    Basées sur les genres des films qu'il a bien notés.
    
    - **user_id**: ID de l'utilisateur
    - **limit**: Nombre de recommandations à retourner
    """
    recommendations = qh.get_user_recommendations(db, user_id, limit)
    return recommendations


# ==================== ROUTES TAGS ====================

@app.get("/movies/{movie_id}/tags", response_model=List[TagSimple], tags=["Tags"])
def get_movie_tags(movie_id: int, db: Session = Depends(get_db)):
    """
    Récupérer tous les tags d'un film.
    
    - **movie_id**: ID du film
    """
    tags = qh.get_movie_tags(db, movie_id)
    if not tags:
        raise HTTPException(status_code=404, detail=f"Aucun tag trouvé pour le film {movie_id}")
    return tags


@app.get("/tags/search", response_model=List[MovieSimple], tags=["Tags"])
def search_by_tag(
    tag: str = Query(..., min_length=1, description="Tag à rechercher"),
    db: Session = Depends(get_db)
):
    """
    Rechercher des films par tag.
    
    - **tag**: Tag à rechercher
    """
    movies = qh.get_movies_by_tag(db, tag)
    if not movies:
        raise HTTPException(status_code=404, detail=f"Aucun film trouvé avec le tag '{tag}'")
    return movies


@app.get("/tags/popular", tags=["Tags"])
def get_popular_tags(
    limit: int = Query(20, ge=1, le=100, description="Nombre de tags à retourner"),
    db: Session = Depends(get_db)
):
    """
    Récupérer les tags les plus populaires.
    
    - **limit**: Nombre de tags à retourner
    """
    popular_tags = qh.get_popular_tags(db, limit)
    return [{"tag": tag, "count": count} for tag, count in popular_tags]


@app.get("/users/{user_id}/tags", response_model=List[TagSimple], tags=["Tags"])
def get_user_tags(user_id: int, db: Session = Depends(get_db)):
    """
    Récupérer tous les tags créés par un utilisateur.
    
    - **user_id**: ID de l'utilisateur
    """
    tags = qh.get_user_tags(db, user_id)
    if not tags:
        raise HTTPException(status_code=404, detail=f"Aucun tag trouvé pour l'utilisateur {user_id}")
    return tags


# ==================== ROUTES LINKS ====================

@app.get("/movies/{movie_id}/links", response_model=LinkSimple, tags=["Links"])
def get_movie_links(movie_id: int, db: Session = Depends(get_db)):
    """
    Récupérer les liens externes (IMDb, TMDb) d'un film.
    
    - **movie_id**: ID du film
    """
    link = qh.get_movie_link(db, movie_id)
    if not link:
        raise HTTPException(status_code=404, detail=f"Aucun lien trouvé pour le film {movie_id}")
    return link


@app.get("/links/imdb/{imdb_id}", response_model=MovieSimple, tags=["Links"])
def get_movie_by_imdb(imdb_id: str, db: Session = Depends(get_db)):
    """
    Récupérer un film par son ID IMDb.
    
    - **imdb_id**: ID IMDb du film (ex: "tt0114709")
    """
    movie = qh.get_movie_by_imdb_id(db, imdb_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Aucun film trouvé avec l'IMDb ID '{imdb_id}'")
    return movie


# ==================== LANCEMENT DE L'APPLICATION ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Active le rechargement automatique en développement
        log_level="info"
    )
