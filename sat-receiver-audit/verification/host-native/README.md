# Додаткові реальні хостові перевірки Linux

Ці звіти отримано на Linux x86_64; це не ARM64 і не фізична Q6A. `rx-worker-smoke.json` перевіряє native ABI fixture/lifecycle/core attributes, `pty-smoke.json` — справжній kernel PTY/termios із переносною моделлю Supervisor. Source hashes у звітах дозволяють звірити їх із кодом. Актуальний ARM64 результат зберігається окремо в ../linux-lab/.

Звіти не створюють hardware acceptance. Native RX fixture не відкриває фізичний SDR; PTY не підтверджує електричний UART чи MCU timing.
