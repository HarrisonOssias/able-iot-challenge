export default function DocsIndex() {
  const items = [
    { slug: 'INGEST_SERVICE', title: 'Ingest Service' },
    { slug: 'ANALYTICS_SERVICE', title: 'Analytics Service' },
    { slug: 'DATABASE', title: 'Database Schema' },
    { slug: 'SYSTEM_DESIGN', title: 'System Design' },
  ];
  return (
    <div style={{ fontFamily: 'system-ui, Arial, sans-serif', padding: 24 }}>
      <h1>Documentation</h1>
      <ul>
        {items.map(i => (
          <li key={i.slug}><a href={`/docs/${i.slug}`} className="font-bold underline hover:no-underline rounded-md px-2 hover:bg-gray-300">{i.title}</a></li>
        ))}
      </ul>
      <p><a href="/">← Back to dashboard</a></p>
    </div>
  );
}


