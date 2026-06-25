from pathlib import Path
from typing import TYPE_CHECKING

from ai_analytics_hub.core.exceptions import DependencyNotInstalledError
from ai_analytics_hub.domain.models import Upload

if TYPE_CHECKING:
    import pandas as pd


def load_dataframe(upload: Upload) -> "pd.DataFrame":
    try:
        import pandas as pd
    except ImportError as error:
        raise DependencyNotInstalledError(
            "Dataset analytics dependencies are not installed. Run 'pip install -e .[analytics]'."
        ) from error

    return pd.read_csv(Path(upload.storage_path))
