from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient
import joblib
import os

app = FastAPI()

ARTIFACT_BUCKET = os.environ["ARTIFACT_BUCKET"]
MODEL_KEY = "artifacts/current/model.joblib"
MODEL_PATH = os.path.expanduser("~/models/model.joblib")


def download_model():
    """
    Tai file model.joblib tu cloud storage ve may khi server khoi dong.

    Ham nay duoc goi mot lan khi module duoc import. CI/local co the dung
    connection string; Azure VM dung system-assigned Managed Identity.
    """
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if connection_string:
        blob = BlobClient.from_connection_string(
            conn_str=connection_string,
            container_name=ARTIFACT_BUCKET,
            blob_name=MODEL_KEY,
        )
    else:
        account_name = os.environ["AZURE_STORAGE_ACCOUNT"]
        blob = BlobClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            container_name=ARTIFACT_BUCKET,
            blob_name=MODEL_KEY,
            credential=DefaultAzureCredential(),
        )
    with open(MODEL_PATH, "wb") as model_file:
        stream = blob.download_blob()
        model_file.write(stream.readall())
    print("Model da duoc tai xuong tu Azure Blob Storage.")


download_model()
model = joblib.load(MODEL_PATH)


class ScoreRequest(BaseModel):
    features: list[float]


@app.get("/healthz")
def healthz():
    """
    Endpoint kiem tra suc khoe server.
    GitHub Actions goi endpoint nay sau khi deploy de xac nhan server dang chay.

    Tra ve: {"status": "ok"}
    """
    return {"status": "ok"}


@app.post("/score")
def score(req: ScoreRequest):
    """
    Endpoint suy luan chinh.

    Dau vao : JSON {"features": [f1, f2, ..., f10]}
    Dau ra  : JSON {"prediction": <0|1>, "label": <"thu_nhap_thap"|"thu_nhap_cao">}

    Thu tu 10 dac trung (khop voi thu tu trong FEATURE_NAMES cua test):
        age, workclass, education_num, marital_status, occupation,
        relationship, sex, capital_gain, capital_loss, hours_per_week
    """
    if len(req.features) != 10:
        raise HTTPException(
            status_code=400,
            detail="Expected 10 features (adult income)",
        )

    prediction = int(model.predict([req.features])[0])
    label = "thu_nhap_cao" if prediction == 1 else "thu_nhap_thap"
    return {"prediction": prediction, "label": label}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
