import fs from 'fs';
import path from 'path';
import type { GetStaticPaths, GetStaticProps } from 'next';
import ReactMarkdown from 'react-markdown';
import Link from 'next/link';

type Props = { content: string; slug: string };

export default function DocPage({ content, slug }: Props) {
  return (
    <div className="prose prose-indigo max-w-none px-6 py-6">
      <Link href="/docs" className="no-underline">← Back</Link>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const root = process.cwd();
  const configured = process.env.DOCS_DIR ? path.resolve(root, process.env.DOCS_DIR) : undefined;
  const candidates = [
    configured,
    path.join(root, 'docs'),        // when docs are inside analytics_service
    path.join(root, '..', 'docs'),  // when docs live at repo root (CI)
  ].filter(Boolean) as string[];

  const docsDir = candidates.find(d => fs.existsSync(d));
  if (!docsDir) {
    return { paths: [], fallback: false };
  }

  const files = fs.readdirSync(docsDir).filter(f => f.endsWith('.md'));
  const paths = files.map(f => ({ params: { doc: f.replace(/\.md$/, '') } }));
  return { paths, fallback: false };
};

export const getStaticProps: GetStaticProps<Props> = async (ctx) => {
  const slug = String(ctx.params?.doc);
  const root = process.cwd();
  const configured = process.env.DOCS_DIR ? path.resolve(root, process.env.DOCS_DIR) : undefined;
  const candidates = [
    configured,
    path.join(root, 'docs'),
    path.join(root, '..', 'docs'),
  ].filter(Boolean) as string[];
  const docsDir = candidates.find(d => fs.existsSync(d));
  const file = docsDir ? path.join(docsDir, `${slug}.md`) : undefined;
  const content = file && fs.existsSync(file) ? fs.readFileSync(file, 'utf-8') : `# Not Found\n\nDocument ${slug} not found.`;
  return { props: { content, slug } };
};


