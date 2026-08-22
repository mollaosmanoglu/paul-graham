import { loader } from 'fumadocs-core/source';
import { lucideIconsPlugin } from 'fumadocs-core/source/lucide-icons';
import type { Folder, Node } from 'fumadocs-core/page-tree';
import { docsContentRoute, docsImageRoute, docsRoute } from './shared';
import { defineDocs } from 'fumadocs-mdx/macro';
import { metaSchema, pageSchema } from 'fumadocs-core/source/schema';

function groupParts(nodes: Node[]): Node[] {
  const out: Node[] = [];
  let part: Folder | undefined;

  for (const node of nodes) {
    if (node.type === 'separator') {
      if (part) out.push(part);
      part = {
        type: 'folder',
        name: node.name,
        $id: `part-${String(node.name)}`,
        defaultOpen: false,
        collapsible: true,
        children: [],
      };
      continue;
    }

    if (part) {
      part.children.push(node);
    } else if (node.type === 'page' && node.url === docsRoute) {
      out.push({ ...node, name: 'Index' });
    } else {
      out.push(node);
    }
  }

  if (part) out.push(part);
  return out;
}

const docs = defineDocs({
  dir: 'content/docs',
  docs: {
    schema: pageSchema,
    postprocess: {
      includeProcessedMarkdown: true,
    },
  },
  meta: {
    schema: metaSchema,
  },
});

// See https://fumadocs.dev/docs/headless/source-api for more info
export const source = loader({
  baseUrl: docsRoute,
  source: docs.toFumadocsSource(),
  plugins: [lucideIconsPlugin()],
  pageTree: {
    transformers: [
      {
        root(node) {
          return { ...node, children: groupParts(node.children) };
        },
      },
    ],
  },
});

export function getPageImageUrl(page: (typeof source)['$inferPage']) {
  const segments = [...page.slugs, 'image.png'];

  return {
    segments,
    url: '/' + [page.locale, ...docsImageRoute.split('/'), ...segments].filter(Boolean).join('/'),
  };
}

export function getPageMarkdownUrl(page: (typeof source)['$inferPage']) {
  const segments = [...page.slugs, 'content.md'];

  return {
    segments,
    url: '/' + [page.locale, ...docsContentRoute.split('/'), ...segments].filter(Boolean).join('/'),
  };
}

export async function getLLMText(page: (typeof source)['$inferPage']) {
  const processed = await page.data.getText('processed');

  return `# ${page.data.title} (${page.url})

${processed}`;
}
