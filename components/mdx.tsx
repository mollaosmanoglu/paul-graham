import defaultMdxComponents from 'fumadocs-ui/mdx';
import type { MDXComponents } from 'mdx/types';
import { IndexIntro } from '@/components/index-intro';
import { Note } from '@/components/note';

export function getMDXComponents(components?: MDXComponents) {
  return {
    ...defaultMdxComponents,
    IndexIntro,
    Note,
    ...components,
  } satisfies MDXComponents;
}

export const useMDXComponents = getMDXComponents;

declare global {
  type MDXProvidedComponents = ReturnType<typeof getMDXComponents>;
}
