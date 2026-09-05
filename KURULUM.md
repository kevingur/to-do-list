# Kurulum

Toplam süre yaklaşık 15 dakika. Hepsi ücretsiz.

## 1. Supabase (veritabanı)

1. supabase.com → hesap aç → **New project**. Bir isim ve veritabanı şifresi seç, bölge olarak Frankfurt (eu-central-1) uygun.
2. Proje hazır olunca sol menüden **SQL Editor** → `schema.sql` dosyasının içeriğini yapıştır → **Run**.
3. **Project Settings → API** sayfasından iki şeyi kopyala:
   - **Project URL**
   - **service_role** anahtarı (secret, `anon` olan değil)

   Bu anahtar tam yetkilidir; sadece Streamlit Secrets'a yazılır, asla kodun içine veya GitHub'a konmaz.

## 2. Yerelde dene (isteğe bağlı)

```
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# secrets.toml içine URL ve anahtarı yaz
pip install -r requirements.txt
streamlit run todo_app.py
```

## 3. GitHub

1. github.com'da **yeni bir private repo** oluştur.
2. Bu klasördeki dosyaları yükle: `todo_app.py`, `requirements.txt`, `schema.sql`, `.gitignore`.
   `.streamlit/secrets.toml` dosyasını **yükleme** (.gitignore zaten engeller).

## 4. Streamlit Community Cloud

1. share.streamlit.io → GitHub ile giriş → **Create app** → **Deploy a public app from GitHub**.
2. Repo'yu ve `todo_app.py` dosyasını seç. Uygulama adresini (`xxx.streamlit.app`) burada belirlersin.
3. **Advanced settings → Secrets** alanına şunu yapıştır:
   ```
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_KEY = "service_role anahtarın"
   ```
4. **Deploy**. 1-2 dakika sonra uygulama yayında.

## 5. Sadece sen görebil

Uygulama ayarlarında (**Settings → Sharing**) "Who can view this app" kısmını **Only specific people** yap ve kendi e-postanı ekle. Giriş Google hesabıyla olur; telefonda bir kez giriş yaparsın, sonra hatırlar.

## 6. Telefon / iPad

Adresi Safari veya Chrome'da aç → **Paylaş → Ana Ekrana Ekle**. Uygulama gibi açılır.

## Notlar

- Ücretsiz planda uygulama birkaç gün kullanılmazsa uyur; ilk açılışta 20-30 saniye bekleme olur, veriler etkilenmez.
- Supabase ücretsiz projeler de 1 hafta hiç istek almazsa duraklatılır; panelden tek tıkla geri açılır. Haftada bir uygulamayı açıyorsan sorun olmaz.
- Verileri ve logu Supabase → **Table Editor**'dan tablo halinde de görebilirsin.
