# onion-romdb

Catálogo de ROMs do [romgi](https://github.com/caprado/romgi) filtrado para os consoles que o Onion OS (Miyoo Mini) emula. Mesmo formato do romgi (SQLite, schema v4), sem a tabela FTS, ~11 MB compactado / ~72 MB no cartão.

| Arquivo | Conteúdo |
|---|---|
| `romdb.db.gz` | Banco SQLite compactado, baixado pelo app ROM Downloader do Onion |
| `version.json` | Versão do romgi de origem + contagens |
| `scripts/filter_romgi.py` | Gera os dois arquivos a partir do banco do romgi |

Plataformas: NES, FDS, SNES, GB, GBC, GBA, Virtual Boy, Pokémon Mini, NDS, Mega Drive, Master System, Game Gear, 32X, Sega CD, PS1, Atari 2600/5200/7800, Lynx, ColecoVision, Intellivision, PC Engine, PC Engine CD, Neo Geo CD. A lista fica em `KEEP` no script e deve bater com `Onion/src/romDownloader/platforms.h`.

## Atualizar

Automático: a Action `Update catalog` roda toda segunda e commita quando a versão do romgi muda. Manual:

```bash
python scripts/filter_romgi.py                      # baixa o romgi e gera na raiz
python scripts/filter_romgi.py caminho/romdb.db.gz  # a partir de um banco local
```

## No Onion

O app lê `https://raw.githubusercontent.com/Brunnexo/onion-romdb/main/{version.json,romdb.db.gz}`. A URL base fica em `.tmp_update/script/romdb_update.sh` (`catalog_url`) e pode ser sobrescrita pelo arquivo `.tmp_update/config/romdl_catalog_url`.
