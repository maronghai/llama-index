"""Run from the book-demo directory: python run.py demo|serve|evaluate|backup."""
import argparse
import json
import logging
import os
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['serve', 'demo', 'evaluate', 'backup', 'worker'])
    parser.add_argument('--output')
    parser.add_argument('--once', action='store_true', help='Process at most one ready job')
    args = parser.parse_args()
    if args.command == 'serve':
        import uvicorn
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        uvicorn.run('kb.api:create_app', factory=True,
                    host=os.getenv('KB_BIND', '127.0.0.1'),
                    port=int(os.getenv('KB_PORT', '8000')), workers=1)
    elif args.command == 'worker':
        from kb.config import Config
        from kb.worker import run_worker
        cfg = Config.from_env()
        cfg.validate()
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        run_worker(cfg, once=args.once)
    elif args.command == 'backup':
        if not args.output:
            parser.error('backup requires --output')
        source = Path(os.getenv('KB_DB', 'data/knowledge.db'))
        target = Path(args.output)
        if not source.exists() or target.exists():
            parser.error('source must exist and backup target must not exist')
        target.parent.mkdir(parents=True, exist_ok=True)
        from contextlib import closing
        with closing(sqlite3.connect(source)) as src, closing(sqlite3.connect(target)) as dst:
            src.backup(dst)
        print('Consistent backup created')
    else:
        from demo import exercise
        report = exercise()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.command == 'evaluate' and not report['passed']:
            raise SystemExit(1)

if __name__ == '__main__':
    main()
