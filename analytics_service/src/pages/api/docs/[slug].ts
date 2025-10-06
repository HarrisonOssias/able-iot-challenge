import fs from 'fs';
import path from 'path';
import type { NextApiRequest, NextApiResponse } from 'next';

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const slug = String(req.query.slug);
    const root = process.cwd();
    const file = path.join(root, 'docs', `${slug}.md`);
    const md = fs.readFileSync(file, 'utf-8');
    res.setHeader('Content-Type', 'text/markdown; charset=utf-8');
    res.status(200).send(md);
  } catch (e: any) {
    res.status(404).json({ error: 'not_found' });
  }
}


