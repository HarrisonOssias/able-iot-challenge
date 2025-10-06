import fs from 'fs';
import path from 'path';
import type { GetStaticPaths, GetStaticProps } from 'next';
import ReactMarkdown from 'react-markdown';

type Props = { content: string; slug: string };

export default function DocPage({ content, slug }: Props) {
  return (
    <div className="prose prose-indigo max-w-none px-6 py-6">
      <a href="/docs" className="no-underline">← Back</a>
      <ReactMarkdown>{content}</ReactMarkdown>
    </div>
  );
}

export const getStaticPaths: GetStaticPaths = async () => {
  const root = process.cwd();
  const docsDir = path.join(root, 'docs');
  const files = fs.readdirSync(docsDir).filter(f => f.endsWith('.md'));
  const paths = files.map(f => ({ params: { doc: f.replace(/\.md$/, '') } }));
  return { paths, fallback: false };
};

export const getStaticProps: GetStaticProps<Props> = async (ctx) => {
  const slug = String(ctx.params?.doc);
  const root = process.cwd();
  const file = path.join(root, 'docs', `${slug}.md`);
  const content = fs.readFileSync(file, 'utf-8');
  return { props: { content, slug } };
};


