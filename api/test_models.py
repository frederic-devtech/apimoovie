# %%
from database import SessionLocal
from models import Movie, Rating, Tag, Link

db = SessionLocal()

# %% 
# Tester la récupération de quelques films
movies = db.query(Movie).limit(10).all()

for movie in movies:
    print(f"ID : {movie.movieId}, Titre : {movie.title}, Genres : {movie.genres}")

else:
    print("No movies found.")

# %%

# Récuperer les films du genre Action
action_movies = db.query(Movie).filter(Movie.genres.like("%Action%")).all()

for movie in action_movies:
    print(f"ID : {movie.movieId}, Titre : {movie.title}, Genres : {movie.genres}")

# %%
# tester la recuperation de quelques évaluations (ratings)
ratings = db.query(Rating).limit(10).all()

for rating in ratings:
    print(f"User ID : {rating.userId}, Movie ID : {rating.movieId}, Rating : {rating.rating}, Timestamp : {rating.timestamp}")


# %%
# Films avec une notre supérieure ou egale à 4
high_rated_movies = db.query(Movie.title, Rating.rating).join(Rating).filter(Rating.rating >= 4.0).limit(5).all()

print(high_rated_movies)


# %%
for title, rating in high_rated_movies:
    print(title, rating)

# %%
# recuperer des tages associés à des films
tags = db.query(Tag).limit(10).all()
for tag in tags:
    print(f"User ID : {tag.userId}, Movie ID : {tag.movieId}, Tag : {tag.tag}, Timestamp : {tag.timestamp}")

# %%
#  Tester la classe link
links = db.query(Link).limit(10).all()
for link in links:
    print(f"Movie ID : {link.movieId}, IMDB ID : {link.imdbId}, TMDB ID : {link.tmdbId}")   

# %%
# fermer la session
db.close()