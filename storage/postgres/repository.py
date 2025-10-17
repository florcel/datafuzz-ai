from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ExampleModel(Base):
    __tablename__ = 'example_table'
    
    id = Column(Integer, Sequence('example_id_seq'), primary_key=True)
    name = Column(String(50))
    value = Column(Integer)

class Repository:
    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def add_example(self, name, value):
        session = self.Session()
        new_example = ExampleModel(name=name, value=value)
        session.add(new_example)
        session.commit()
        session.close()

    def get_example(self, example_id):
        session = self.Session()
        example = session.query(ExampleModel).filter(ExampleModel.id == example_id).first()
        session.close()
        return example

    def get_all_examples(self):
        session = self.Session()
        examples = session.query(ExampleModel).all()
        session.close()
        return examples

    def delete_example(self, example_id):
        session = self.Session()
        example = session.query(ExampleModel).filter(ExampleModel.id == example_id).first()
        if example:
            session.delete(example)
            session.commit()
        session.close()