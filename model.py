from keras.models import Sequential
from keras import layers
from keras.preprocessing.text import Tokenizer
from keras.models import load_model
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score
from nltk.corpus import stopwords
import nltk
import pickle

class SQLIModel:
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
    
    def create_model(self, input_dim):
        model = Sequential()
        model.add(layers.Dense(20, input_dim=input_dim, activation='relu'))
        model.add(layers.Dense(10,  activation='tanh'))
        model.add(layers.Dense(1024, activation='relu'))
        model.add(layers.BatchNormalization())
        model.add(layers.Dropout(0.5))
        model.add(layers.Dense(1, activation='sigmoid'))

        model.compile(loss='binary_crossentropy', 
                      optimizer='adam', 
                      metrics=['accuracy'])
        return model

    def train_model(self, csv_file_path, model_file_path, vectorizer_file_path):
        # Load dataset
        df = pd.read_csv(csv_file_path, encoding='utf-16')
        nltk.download('stopwords')
        self.vectorizer = CountVectorizer(min_df=2, max_df=0.7, stop_words='english')
        posts = self.vectorizer.fit_transform(df['Sentence'].values.astype('U')).toarray()
        transformed_posts = pd.DataFrame(posts, columns=self.vectorizer.get_feature_names_out())
        df = pd.concat([df, transformed_posts], axis=1)
        X = df[df.columns[2:]]
        y = df['Label']
        # Split dataset into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        # Create model
        input_dim = X_train.shape[1]  # Number of features
        self.model = self.create_model(input_dim)
        # Train model
        classifier_nn = self.model.fit(X_train, y_train,
                                  epochs=10,
                                  verbose=True,
                                  validation_data=(X_test, y_test),
                                  batch_size=15)
        # Make predictions
        y_pred = self.model.predict(X_test)
        y_pred = [1 if p >= 0.5 else 0 for p in y_pred]
        # Evaluate model
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        print("Accuracy: {0:.4f}, Precision: {1:.4f}, Recall: {2:.4f}".format(accuracy, precision, recall))
        # Save model and vectorizer
        self.model.save(model_file_path)
        with open(vectorizer_file_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        return self.model

    def load_vectorizer(self, model_file_path, vectorizer_file_path):
        self.model = load_model(model_file_path)
        with open(vectorizer_file_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
            

    def is_sqli(self, sentence, model,model_file_path, vectorizer_file_path):
        if not self.model or not self.vectorizer:
            self.load_vectorizer(model_file_path, vectorizer_file_path)
        sentence_fit = self.vectorizer.transform([sentence]).toarray()
        sentence_df = pd.DataFrame(sentence_fit, columns=self.vectorizer.get_feature_names_out())
        # Ensure that the columns are in the same order as during training
        sentence_df = sentence_df[self.vectorizer.get_feature_names_out()]
        if model.predict(sentence_df)[0][0] >= 0.95:
            is_malicious = True
        else:
            is_malicious = False
        return is_malicious

