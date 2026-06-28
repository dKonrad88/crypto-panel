# Crypto Panel

Painel pessoal e sóbrio para acompanhar 6 criptoativos — **BTC, ETH, SOL, BNB, XRP, SUI** —
com preço, indicadores técnicos, tendência, dados on-chain e **backtest** integrado.
Uso individual, **não é recomendação de investimento**.

## Telas
- **Painel** — preço (USDT), variação 24h/7d/30d, EMA 20/50/200, RSI, MACD, volume, tendência curto/médio e on-chain resumido.
- **Backtest** — motor nativo (EMA/SMA cross, RSI, MACD, Bollinger, tendência>EMA200) com métricas
  (retorno vs buy&hold, win rate, drawdown, Sharpe, exposição), tabela de trades, curva de capital e otimização.
  Inclui gráfico do **TradingView** embutido + atalho para o Strategy Tester deles.
- **On-chain** — hashrate/fees/mempool (BTC) e TVL com histórico (DefiLlama).

## Como funciona
- **Front estático** (`index.html`, HTML/JS puro, sem build) — roda em qualquer navegador.
- Preço/candles/indicadores/backtest: **Binance** (sem chave; fallback `data-api.binance.vision`).
- On-chain grátis: **DefiLlama** (TVL + histórico) e **mempool.space** (BTC).
- **Coletor** (`collector/collect.py`, Python stdlib) roda no **GitHub Actions** de hora em hora,
  acumula histórico on-chain e cacheia preço/candles (fallback para redes que bloqueiam a Binance).

Métricas on-chain "inteligentes" (netflow de exchange, SOPR, MVRV) são pagas e ficam **fora** deste projeto.

## Rodar localmente
```bash
cd crypto-panel
python3 -m http.server 8765
# abrir http://localhost:8765
```

## Publicação
GitHub Pages (branch `main`, raiz). Sem segredos no front — chaves (quando houver) ficam nos Secrets do Actions.
