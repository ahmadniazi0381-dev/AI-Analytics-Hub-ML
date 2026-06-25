from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from ai_analytics_hub.core.exceptions import DependencyNotInstalledError
from ai_analytics_hub.domain.models import Upload
from ai_analytics_hub.services.dataset_service import load_dataframe

if TYPE_CHECKING:
    import numpy as np


def train_classifier(
    *,
    upload: Upload,
    target_column: str,
    epochs: int,
    batch_size: int,
    test_size: float,
    report_dir: str,
) -> dict:
    try:
        import numpy as np
        import tensorflow as tf
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
    except ImportError as error:
        raise DependencyNotInstalledError(
            "Classifier dependencies are not installed. Run 'pip install -e .[analytics,training]'."
        ) from error

    dataframe = load_dataframe(upload)
    target_column = target_column.strip()
    if target_column not in dataframe.columns:
        raise ValueError(f"Target column '{target_column}' was not found in the uploaded dataset.")

    features = dataframe.drop(columns=[target_column])
    targets = dataframe[target_column]

    numeric_columns = features.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = [column for column in features.columns if column not in numeric_columns]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_columns),
            ("cat", categorical_pipeline, categorical_columns),
        ]
    )

    label_encoder = LabelEncoder()
    encoded_targets = label_encoder.fit_transform(targets.astype(str))

    unique_classes, class_counts = np.unique(encoded_targets, return_counts=True)
    should_stratify = len(unique_classes) > 1 and len(class_counts) > 0 and np.min(class_counts) >= 2

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        encoded_targets,
        test_size=test_size,
        stratify=encoded_targets if should_stratify else None,
        random_state=42,
    )

    x_train_processed = preprocessor.fit_transform(x_train)
    x_test_processed = preprocessor.transform(x_test)
    if hasattr(x_train_processed, "toarray"):
        x_train_processed = x_train_processed.toarray()
        x_test_processed = x_test_processed.toarray()

    model = _build_model(
        input_dim=x_train_processed.shape[1],
        num_classes=len(label_encoder.classes_),
    )
    history = model.fit(
        x_train_processed,
        _prepare_targets(y_train, len(label_encoder.classes_)),
        validation_split=0.1,
        epochs=epochs,
        batch_size=batch_size,
        verbose=0,
    )

    probability_predictions = model.predict(x_test_processed, verbose=0)
    predicted_labels = _decode_predictions(probability_predictions, len(label_encoder.classes_))

    precision, recall, f1_score, _ = precision_recall_fscore_support(
        y_test,
        predicted_labels,
        average="weighted",
        zero_division=0,
    )
    accuracy = accuracy_score(y_test, predicted_labels)
    matrix = confusion_matrix(y_test, predicted_labels).tolist()

    artifact_path = Path(report_dir) / f"classifier-{uuid4()}.keras"
    model.save(artifact_path)

    return {
        "metrics": {
            "accuracy": round(float(accuracy), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1_score": round(float(f1_score), 4),
        },
        "class_labels": label_encoder.classes_.tolist(),
        "confusion_matrix": matrix,
        "history": {
            "accuracy": [round(float(value), 4) for value in history.history.get("accuracy", [])],
            "val_accuracy": [
                round(float(value), 4) for value in history.history.get("val_accuracy", [])
            ],
            "loss": [round(float(value), 4) for value in history.history.get("loss", [])],
            "val_loss": [round(float(value), 4) for value in history.history.get("val_loss", [])],
        },
        "artifact_path": str(artifact_path),
    }


def _build_model(*, input_dim: int, num_classes: int):
    try:
        from tensorflow import keras
    except ImportError as error:
        raise DependencyNotInstalledError(
            "Classifier dependencies are not installed. Run 'pip install -e .[training]'."
        ) from error

    layers = [
        keras.layers.Input(shape=(input_dim,)),
        keras.layers.Dense(64, activation="relu"),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dense(16, activation="relu"),
    ]
    if num_classes <= 2:
        layers.append(keras.layers.Dense(1, activation="sigmoid"))
        loss = "binary_crossentropy"
    else:
        layers.append(keras.layers.Dense(num_classes, activation="softmax"))
        loss = "categorical_crossentropy"

    model = keras.Sequential(layers)
    model.compile(optimizer="adam", loss=loss, metrics=["accuracy"])
    return model


def _prepare_targets(targets: "np.ndarray", num_classes: int):
    try:
        from tensorflow import keras
    except ImportError as error:
        raise DependencyNotInstalledError(
            "Classifier dependencies are not installed. Run 'pip install -e .[training]'."
        ) from error

    if num_classes <= 2:
        return targets
    return keras.utils.to_categorical(targets, num_classes=num_classes)


def _decode_predictions(probabilities, num_classes: int) -> "np.ndarray":
    if num_classes <= 2:
        return (probabilities.flatten() >= 0.5).astype(int)
    return probabilities.argmax(axis=1)
