from database import SessionLocal
from api import query_helpers as query_helpers


db = SessionLocal()

movies = query_helpers.get_movies(db, title="Inception", genre="Sci-Fi", limit=5)

for movie in movies:
    print(f"Movie ID: {movie.movieId}, Title: {movie.title}, Genres: {movie.genres}")   



db.close()

