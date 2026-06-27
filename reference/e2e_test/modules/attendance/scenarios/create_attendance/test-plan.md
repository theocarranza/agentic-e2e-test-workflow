# Test Plan — create_attendance

**Propósito:** Verificar que um terapeuta consegue iniciar um atendimento via wizard, registrar uma anotação na sessão em andamento, finalizar o atendimento e confirmar que a anotação persiste na aba "Anotações" da página de detalhes.

---

**Módulo:** Atendimento (`attendance`)

**Ambiente & seed:**

- Conta: `Instituto Beta`
- Usuário: `criador@beta.bhave.life` (perfil Terapeuta)
- Estudante: `Breno Segundo`
- Pré-condição de dados: o estudante possui programas ativos e ao menos uma folha estruturada disponível no seed (necessário para que as páginas 1, 2 e 3 do wizard sejam exibidas corretamente; as seleções podem ficar vazias — o cenário as ignora)

---

```gherkin
Feature: Criar atendimento — caminho feliz
  Como terapeuta autenticado no perfil Instituto Beta
  Quero iniciar um atendimento para o estudante Breno Segundo via wizard,
  registrar uma anotação durante a sessão e finalizar o atendimento
  Para que a anotação clínica esteja disponível nos detalhes do atendimento encerrado

  Background:
    Given que estou autenticado como "criador@beta.bhave.life" no perfil "Instituto Beta"
    And estou na página de detalhes do estudante "Breno Segundo"
    And não existe nenhum atendimento em andamento para esse estudante nesta sessão

  @small
  Scenario: Terapeuta inicia wizard, registra nota e finaliza — nota persiste nos detalhes
    # Etapa 1 — Wizard de configuração
    When aciono o botão de iniciar novo atendimento na página de detalhes do estudante
    Then o wizard de novo atendimento é aberto

    # Etapa 1.1 — Folhas estruturadas (pulado)
    When avanço sem selecionar nenhuma folha estruturada
    Then o wizard exibe a etapa de seleção de comportamentos de aquisição

    # Etapa 1.2 — Livre operante (pulado)
    When avanço sem selecionar nenhum comportamento de aquisição
    Then o wizard exibe a etapa de seleção de comportamentos interferentes com o botão "Iniciar atendimento"

    # Etapa 1.3 — Iniciar
    When confirmo o início do atendimento sem selecionar comportamentos interferentes
    Then o sistema registra a intenção de iniciar o atendimento
    And o atendimento entra em andamento
    And a tela de atendimento em andamento é exibida com o temporizador ativo e o botão "Finalizar" visível

    # Etapa 2 — Aba Anotações
    When navego para a aba "Anotações" da sessão em andamento
    Then o campo de entrada de anotação está disponível

    When digito a anotação "<texto_da_nota>" e envio
    Then a anotação "<texto_da_nota>" aparece imediatamente na lista de anotações da sessão em andamento

    # Etapa 3 — Finalizar atendimento
    When aciono o botão "Finalizar" da sessão
    Then um diálogo de confirmação informa que todos os registros estão salvos

    When confirmo a finalização no diálogo
    Then o atendimento é encerrado com status "finished"
    And a tela de detalhes do atendimento é exibida

    # Etapa 4 — Verificação adversarial de persistência
    When navego até a aba "Anotações" nos detalhes do atendimento encerrado
    Then a anotação "<texto_da_nota>" está visível e persiste como registro clínico do atendimento

    Examples:
      | texto_da_nota                                     |
      | Estudante demonstrou boa atenção durante a sessão |
```

---

## Notas para a implementação

### Premissas

- O seed garante que `criador@beta.bhave.life` é Criador do perfil `Instituto Beta`, tem acesso ao estudante `Breno Segundo` e pode iniciar atendimentos para esse estudante.
- Nenhum atendimento agendado está pendente para o estudante no dia de execução do teste; caso contrário, o botão de iniciar exibe um diálogo de seleção de atendimento agendado em vez de abrir o wizard diretamente, alterando o fluxo.

### Fontes dos `Given`

| Dado                                | Fonte                                             |
| ----------------------------------- | ------------------------------------------------- |
| Usuário `criador@beta.bhave.life`   | Seed de autenticação do ambiente de teste         |
| Perfil `Instituto Beta`             | Seed de conta/perfil                              |
| Estudante `Breno Segundo`           | Seed de estudante com programas ativos            |
| Permissão de criação de atendimento | Seed de permissões do perfil `Instituto Beta`     |
