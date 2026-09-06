# Telefona push bildirimi (ntfy)

Her sabah 08:00'de o günün ve gecikmiş görevleri telefona bildirim olarak gelir.
Görev yoksa mesaj gelmez.

## 1. Telefona ntfy uygulamasını kur
App Store / Google Play → **ntfy**. Ücretsiz, hesap gerekmez.

## 2. Bir konu (topic) adı seç
ntfy.sh'de konular herkese açıktır: adı bilen okur ve yazar. O yüzden tahmin
edilemeyecek bir ad kullan, örn. `todo-abdullah-k9x2m7q4`.
Uygulamada **+ Subscribe to topic** → bu adı yaz. Bu kadar.

## 3. GitHub'a dosyaları yükle
- `notify.py` (repo köküne)
- `.github/workflows/notify.yml` (klasörleriyle birlikte; GitHub'da
  "Add file → Create new file" deyip dosya adına `.github/workflows/notify.yml`
  yazarsan klasörleri kendisi açar)

## 4. GitHub Secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Üç tane ekle (değerler Streamlit Secrets'takilerle aynı):

| Name          | Value                              |
|---------------|------------------------------------|
| SUPABASE_URL  | https://xxxx.supabase.co           |
| SUPABASE_KEY  | service_role anahtarı              |
| NTFY_TOPIC    | 2. adımda seçtiğin konu adı        |

## 5. Test
Repo → **Actions** sekmesi → soldan "Daily task notification" → **Run workflow**.
Birkaç saniye içinde telefona bildirim gelmeli (bugün görev varsa).
Actions sekmesi ilk kez kapalıysa "I understand… enable them" düğmesine bas.

## Ayarlar
- Saat: `notify.yml` içindeki `cron: "0 5 * * *"` (UTC). 07:00 TR → `"0 4 * * *"`,
  09:00 TR → `"0 6 * * *"`. GitHub zamanlamayı bazen 5-15 dk geciktirir.
- Boş günlerde de mesaj istersen `notify.py` içinde `SEND_WHEN_EMPTY = True`.
- Ek fayda: her sabah veritabanına istek gittiği için Supabase hiç uyumaz.
