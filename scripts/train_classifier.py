"""
Trains the intent classifier used by the agent's routing layer.

Reads data/aea_dataset.csv, and trains multiple models:
1. TF-IDF + Logistic Regression
2. TF-IDF + Naive Bayes
3. Sentence Transformers + Logistic Regression

Saves all to models/intent_classifier.pkl.
"""

import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sentence_transformers import SentenceTransformer

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "aea_dataset.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "intent_classifier.pkl")

def main():
    df = pd.read_csv(DATA_PATH)
    single_intent_df = df[~df["task_category"].str.contains(r"\+")]

    X = single_intent_df["user_instruction"]
    y = single_intent_df["task_category"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 1. TF-IDF + Logistic Regression
    print("Training TF-IDF + Logistic Regression...")
    tfidf = TfidfVectorizer(lowercase=True, ngram_range=(1, 3), stop_words="english", min_df=1)
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)

    lr_model = LogisticRegression(max_iter=1000)
    lr_model.fit(X_train_tfidf, y_train)
    print(f"  Accuracy: {accuracy_score(y_test, lr_model.predict(X_test_tfidf)):.2f}")

    # 2. TF-IDF + Naive Bayes
    print("Training TF-IDF + Naive Bayes...")
    nb_model = MultinomialNB()
    nb_model.fit(X_train_tfidf, y_train)
    print(f"  Accuracy: {accuracy_score(y_test, nb_model.predict(X_test_tfidf)):.2f}")

    # 3. Sentence Transformers + Logistic Regression
    print("Training Sentence Transformers + Logistic Regression...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    X_train_emb = embedder.encode(X_train.tolist())
    X_test_emb = embedder.encode(X_test.tolist())
    
    st_lr_model = LogisticRegression(max_iter=1000)
    st_lr_model.fit(X_train_emb, y_train)
    print(f"  Accuracy: {accuracy_score(y_test, st_lr_model.predict(X_test_emb)):.2f}")

    # Save everything
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({
        "tfidf_vectorizer": tfidf,
        "lr_model": lr_model,
        "nb_model": nb_model,
        "st_lr_model": st_lr_model,
    }, MODEL_PATH)
    print(f"Saved trained pipelines to {MODEL_PATH}")

if __name__ == "__main__":
    main()