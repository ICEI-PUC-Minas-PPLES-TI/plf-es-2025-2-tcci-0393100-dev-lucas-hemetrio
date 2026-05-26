jest.mock('@/services/knowledgeService', () => ({
  knowledgeService: {
    getNodeMentions: jest.fn(),
    getEdgeCoOccurrences: jest.fn(),
  },
}));

import { render, screen } from '@testing-library/react-native';

import EntityContextDrawer from '@/components/EntityContextDrawer';
import { knowledgeService } from '@/services/knowledgeService';

const mockGetNodeMentions = knowledgeService.getNodeMentions as jest.Mock;

describe('EntityContextDrawer', () => {
  beforeEach(() => mockGetNodeMentions.mockReset());

  // US 09: ao selecionar um nó do grafo, o painel de contexto carrega e exibe
  // a entidade (título + tipo) e suas menções.
  it('carrega e exibe o cabeçalho da entidade ao selecionar um nó', async () => {
    mockGetNodeMentions.mockResolvedValue({
      node: { uid: 'n1', text: 'Brasil', label: 'LOC', mention_count: 2 },
      mentions: [
        {
          uid: 'm1',
          sentence_text: 'O Brasil é grande.',
          source_type: 'document',
          source_uid: 'd1',
          source_title: 'Geografia',
          page_number: 3,
        },
      ],
    });

    render(
      <EntityContextDrawer
        projectUid="p1"
        selection={{ type: 'node', uid: 'n1' }}
        onClose={jest.fn()}
        onNavigateToTarget={jest.fn()}
      />,
    );

    // subtitle só aparece após o carregamento concluir
    expect(await screen.findByText(/2 menç/)).toBeTruthy();
    expect(screen.getByText('LOC')).toBeTruthy(); // badge do tipo da entidade
    expect(screen.getAllByText('Brasil').length).toBeGreaterThanOrEqual(1);
    expect(mockGetNodeMentions).toHaveBeenCalledWith('p1', 'n1', expect.anything());
  });
});
