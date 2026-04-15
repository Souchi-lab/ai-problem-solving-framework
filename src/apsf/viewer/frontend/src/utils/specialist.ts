import type { SpecialistCandidatesData, SpecialistCandidateItem, CreateSpecialistResult } from '../types'
import { extractMarkdownSection } from './markdown'

// Parse P/B/C specialist codes from execution-assignment.md text
export function parseSpecialistCodes(content: string): { planner: string; builder: string; critic: string } {
  const extract = (prefix: string) => {
    const m = content.match(new RegExp(`${prefix}-TYPE:\\s*([A-Z][A-Z0-9-]+)`, 'i'))
    return m ? m[1].trim() : ''
  }
  return { planner: extract('P'), builder: extract('B'), critic: extract('C') }
}

export function deriveSpecialistPathPreview(role: SpecialistCandidatesData['role'], code: string, slug: string) {
  const normalizedSlug = slug
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-')

  const directory =
    role === 'Planner'
      ? 'framework/agents/planners'
      : role === 'Builder'
        ? 'framework/agents/builders'
        : role === 'Critic'
          ? 'framework/agents/critics'
          : ''

  if (!directory || !code.trim() || !normalizedSlug) return ''
  return `${directory}/${normalizedSlug}.md`
}

export function slugifySpecialistName(raw: string) {
  return raw
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .replace(/-{2,}/g, '-')
}

export function defaultSpecialistTitle(role: 'Planner' | 'Builder' | 'Critic') {
  return role === 'Planner'
    ? 'Verification Planning Planner'
    : role === 'Builder'
      ? 'Verification Reliability Builder'
      : 'Verification Reliability Critic'
}

export function buildSpecialistMarkdownTemplate({
  role,
  specialistCode,
  title,
  scope,
  useWhen,
  outOfScope,
  evaluationCriteria,
}: {
  role: 'Planner' | 'Builder' | 'Critic'
  specialistCode: string
  title: string
  scope: string
  useWhen: string
  outOfScope: string
  evaluationCriteria: string
}) {
  const resolvedTitle = title.trim() || defaultSpecialistTitle(role)
  const resolvedCode = specialistCode.trim() || (role === 'Planner' ? 'P-13' : role === 'Builder' ? 'B-08' : 'C-09')
  const roleLabel = role
  return [
    `# Specialist: ${resolvedTitle} (${resolvedCode})`,
    '',
    `You are the ${resolvedTitle}.`,
    '',
    '## Scope',
    '',
    scope.trim() || '[Describe the specialist boundary and primary responsibility.]',
    '',
    '## Use This Specialist When',
    '',
    useWhen.trim() || '[Describe the situations where this specialist should be chosen.]',
    '',
    '## Out of Scope',
    '',
    outOfScope.trim() || '[Describe what this specialist should not cover.]',
    '',
    '## Evaluation Criteria',
    '',
    evaluationCriteria.trim() || '[Describe how good output should be judged.]',
    '',
    '## Output Style',
    '',
    `- Stay within the ${roleLabel} role boundary.`,
    '- Keep recommendations concrete, scoped, and reviewable.',
  ].join('\n')
}

export function parseSpecialistMarkdownImport(markdown: string, role: 'Planner' | 'Builder' | 'Critic') {
  const headerMatch = markdown.match(/^#\s+Specialist:\s*(.+?)\s*\(([A-Z]-\d{2})\)\s*$/im)
  const title = headerMatch?.[1]?.trim() ?? ''
  const specialistCode = headerMatch?.[2]?.trim() ?? ''
  const scope = extractMarkdownSection(markdown, 'Scope')
  const useWhen = extractMarkdownSection(markdown, 'Use This Specialist When')
  const outOfScope = extractMarkdownSection(markdown, 'Out of Scope')
  const evaluationCriteria = extractMarkdownSection(markdown, 'Evaluation Criteria')
  const inferredSlug = slugifySpecialistName(title)

  if (!title && !scope && !useWhen && !outOfScope && !evaluationCriteria) {
    return {
      error: `Could not parse a specialist markdown template for ${role}.`,
    }
  }

  return {
    specialistCode,
    title,
    slug: inferredSlug,
    scope,
    useWhen,
    outOfScope,
    evaluationCriteria,
  }
}

export function validateImportedSpecialistDraft(
  parsed: ReturnType<typeof parseSpecialistMarkdownImport>,
  role: 'Planner' | 'Builder' | 'Critic',
) {
  if ('error' in parsed) {
    return {
      ok: false,
      severity: 'error' as const,
      message: parsed.error ?? `Could not parse a specialist markdown template for ${role}.`,
    }
  }

  const expectedPrefix = role === 'Planner' ? 'P-' : role === 'Builder' ? 'B-' : 'C-'
  const issues: string[] = []

  if (!parsed.specialistCode) {
    issues.push(`missing specialist code in header; expected ${expectedPrefix}xx`)
  } else if (!new RegExp(`^${expectedPrefix}\\d{2}$`, 'i').test(parsed.specialistCode)) {
    issues.push(`code ${parsed.specialistCode} does not match role ${role}; expected prefix ${expectedPrefix}`)
  }

  if (!parsed.title.trim()) {
    issues.push('missing title in header')
  }

  if (!parsed.slug.trim()) {
    issues.push('could not derive a valid slug from the title')
  }

  if (issues.length > 0) {
    return {
      ok: false,
      severity: 'warning' as const,
      message: `Prefill applied with validation issues: ${issues.join('; ')}. Review the fields before creating.`,
    }
  }

  return {
    ok: true,
    severity: 'success' as const,
    message: `Markdown prefill is valid for ${role}. Review the fields, then create a new specialist asset if needed.`,
  }
}

export function mergeCreatedSpecialistCandidate(
  data: SpecialistCandidatesData | null,
  result: CreateSpecialistResult,
): SpecialistCandidatesData | null {
  if (!data || data.role !== result.role) return data
  if (data.candidates.some((candidate) => candidate.code === result.specialist_code)) {
    return data
  }

  const createdCandidate: SpecialistCandidateItem = {
    code: result.specialist_code,
    name: result.title,
    score: 0,
    reason: 'Newly created specialist for this session. Assign explicitly if this run should use it.',
    use_when: result.use_when,
    path: result.relative_path,
    scope: result.scope,
    out_of_scope: result.out_of_scope,
    evaluation_criteria: result.evaluation_criteria,
    is_recommended: false,
    is_current: false,
  }

  return {
    ...data,
    candidates: [createdCandidate, ...data.candidates],
  }
}
