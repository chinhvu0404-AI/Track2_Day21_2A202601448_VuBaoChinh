# Triển khai lab trên Azure

Không commit connection string, private SSH key hay nội dung GitHub Secrets.

## Tài nguyên Azure

| Thành phần | Giá trị |
|---|---|
| Resource group | `rg-income-lab` |
| Region | `eastasia` |
| Storage account | `incomechinh448` |
| Blob container | `income-lab` |
| DVC remote | `azure://income-lab/dvc` |
| Model blob | `artifacts/current/model.joblib` |
| VM | `income-api` |

Lấy connection string vào biến môi trường hiện tại, không ghi vào file đã track:

```powershell
$env:AZURE_STORAGE_CONNECTION_STRING = az storage account show-connection-string `
  --resource-group rg-income-lab --name incomechinh448 --query connectionString -o tsv
```

## DVC

Sau khi đã chạy `python prepare_data.py`:

```powershell
dvc init
dvc remote add -d labstore azure://income-lab/dvc
dvc remote modify --local labstore connection_string "$env:AZURE_STORAGE_CONNECTION_STRING"
dvc add data/train_batch1.csv data/holdout.csv data/train_batch2.csv
git add .dvc .gitignore data/*.dvc
git commit -m "feat: track datasets with DVC"
dvc push
```

`--local` giữ connection string trong `.dvc/config.local`, là file bị Git bỏ qua.

## VM và service

Tạo Ubuntu VM và mở cổng API:

```powershell
az vm create --resource-group rg-income-lab --name income-api --image Ubuntu2204 `
  --size Standard_B1s --admin-username azureuser --generate-ssh-keys
az vm open-port --resource-group rg-income-lab --name income-api --port 8080 --priority 1001
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\income_deploy -N "" -C "github-actions-deploy"
```

Copy public key deploy vào `~/.ssh/authorized_keys` của `azureuser`; copy `src/serve.py` vào `~/src/serve.py`.
Trên VM cài runtime, tạo `~/models` và file `/etc/income-api.env` quyền `600`, chứa hai dòng
`ARTIFACT_BUCKET=income-lab` và `AZURE_STORAGE_CONNECTION_STRING=<CONNECTION_STRING>`.

Tạo `/etc/systemd/system/income-api.service`:

```ini
[Unit]
Description=Income Model Inference Server
After=network.target

[Service]
User=azureuser
WorkingDirectory=/home/azureuser
EnvironmentFile=/etc/income-api.env
ExecStart=/usr/bin/python3 /home/azureuser/src/serve.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Sau workflow xanh đầu tiên:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now income-api
sudo journalctl -u income-api -n 50 --no-pager
```

## GitHub Secrets

| Secret | Giá trị |
|---|---|
| `STORAGE_CREDENTIALS` | Azure Storage connection string |
| `ARTIFACT_BUCKET` | `income-lab` |
| `SERVER_HOST` | Public IP của `income-api` |
| `SERVER_USER` | `azureuser` |
| `SERVER_SSH_KEY` | nội dung private key `income_deploy` |

Sau khi workflow xanh, kiểm tra:

```bash
curl http://<VM_PUBLIC_IP>:8080/healthz
curl -X POST http://<VM_PUBLIC_IP>:8080/score -H "Content-Type: application/json" -d '{"features":[28,2,14,2,11,0,1,0,0,45]}'
```

Để kích hoạt Bước 3, luôn dùng thứ tự `append_batch.py → dvc add → dvc push → git push`.
