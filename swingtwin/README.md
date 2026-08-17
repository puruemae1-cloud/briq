# TwinSwing

UK golf app. **Not part of Briq.**

A subscriber films their swing, then uploads the PGA (or LPGA) clip they want to look like. TwinSwing plays the two videos together, scores the gaps, and — for paying members — keeps a daily plan and a match-score history.

## Product

| | Trial | TwinSwing+ (£12.99 / month, or £99 / year) |
|---|---|---|
| Compare | One pair | Unlimited |
| Their clip | Upload any tour slow-mo | Same |
| Report | Three differences | Every phase + drills |
| 3D | Face-on + down-the-line | Same, kept in history |
| Daily / sheet | — | Yes |

Clips are read on the device in this prototype. They are not sent to Briq or to a shop backend.

Player labels (Rory, Scheffler, Morikawa, …) are only so the coaching copy matches who you are copying. The actual comparison uses **your file versus their file**. Instagram accounts such as [@purego1f](https://www.instagram.com/purego1f) are a source of slow-mo to save onto the phone — we do not scrape Instagram.

## Run locally

```bash
cd swingtwin
npm install
npm run dev
```

App: [http://localhost:3001](http://localhost:3001)

Installable as a PWA (Add to Home Screen) while native stores are in progress.

## UK shipping (next)

1. Register a UK company (England and Wales) and a privacy policy under UK GDPR.
2. Stripe Billing in GBP (or App Store / Play billing once native).
3. Expo (SDK 57+) iOS + Android using the same compare flow — camera roll for both videos, `expo-video` for side-by-side.
4. Optional later: on-device pose (MediaPipe / TFLite) instead of motion silhouettes.

Do not deploy this folder with the Briq Vercel project. It is a separate product and a separate domain.
