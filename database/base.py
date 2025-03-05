from sqlalchemy.orm import declarative_base

Base = declarative_base()
# TODO This is probably not the best way, but I needed a general place to have my Base class instantiated as I created a different one in each model which might have caused issues.