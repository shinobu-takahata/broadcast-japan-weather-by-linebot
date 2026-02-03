# 要求定義: 天気API切り替え（OpenWeatherMap → WeatherAPI）

## 概要
天気データの取得元を OpenWeatherMap API から WeatherAPI（https://api.weatherapi.com/v1）に切り替える。
降水確率は引き続き JMA（気象庁）API から取得する。

## 背景・目的
- 天気データの取得元APIを WeatherAPI に統一し、他プロジェクトとの一貫性を保つ
- WeatherAPI は1時間ごとの予報データを提供しており、09:00〜23:00のフィルタリングに適している

## 変更内容
- OpenWeatherMap API クライアントを WeatherAPI クライアントに置き換える
- WeatherAPI のレスポンス構造に合わせて気温データの取得・加工ロジックを変更する
- 降水確率の取得は JMA API を継続使用する（変更なし）

## 受け入れ条件
1. WeatherAPI（https://api.weatherapi.com/v1/forecast.json）から1時間ごとの気温データを取得できること
2. 09:00〜23:00 JST の時間帯でフィルタリングし、最高気温・最低気温を算出できること
3. 降水確率は従来通り JMA API から取得し、変更がないこと
4. 既存の Weather バリューオブジェクト（max_temp, min_temp, pop）の構造に変更がないこと
5. LINE メッセージのフォーマットに変更がないこと
6. エラーハンドリング（リトライ・指数バックオフ）が従来と同等であること
7. Secrets Manager から WeatherAPI の API キーを取得できること
8. 既存のテストが WeatherAPI の構造に合わせて更新され、すべてパスすること

## 制約事項
- WeatherAPI の無料プランの API レート制限を考慮すること
- 既存の JMA 連携ロジック（降水確率取得）には手を加えないこと
- ドメイン層のバリューオブジェクト（Weather, Location）の構造は変更しないこと
