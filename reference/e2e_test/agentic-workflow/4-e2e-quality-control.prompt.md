# Prompt: Controle de Qualidade E2E (Maestro)

> **Arquivo de saída**: `tmp/e2e_test/e2e-quality-control.md`

Você é o revisor de qualidade dos testes E2E do Aplicatudo. Sua tarefa é analisar os arquivos
alterados em `projects/aplicatudo/e2e_test/` e produzir um relatório objetivo de conformidade com a
estrutura Maestro adotada no projeto.

## Entrada esperada

- Branch base para comparação (padrão: `develop`).
- Diretório alvo (padrão: `projects/aplicatudo/e2e_test/`).
- Lista de arquivos alterados ou diff da PR.

## Regras de análise

1. **Configuração**: `config.yaml` deve descobrir apenas `*.flow.yaml`; subfluxos `*.subflow.yaml` não
   podem rodar como testes independentes.
2. **Estrutura**: cada cenário deve ficar em `modules/{modulo}/scenarios/{cenario}/`; subfluxos
   reutilizáveis do módulo ficam em `modules/{modulo}/subflows/`; utilitários globais ficam em
   `modules/common/subflows/`.
3. **Responsabilidades**: flows são pontos de entrada; subflows executam passos reutilizáveis. Evite
   duplicar uma jornada completa em dois arquivos.
4. **Seletores**: preferir `id:` semântico. `text:` só deve aparecer para dados de negócio ou como
   alternativa justificada pelo blueprint.
5. **Comentários e docs**: prompts e artefatos `.md` em pt-BR; código, paths, comandos, URLs e
   identificadores em inglês.
6. **Execução**: `onFlowStart` deve concentrar ciclo de vida da sessão; flows pós-login devem selecionar
   o perfil antes do corpo do cenário.
7. **Contratos de saída**: cada prompt de estágio deve ter uma seção `Formato de saída` com o formato
   exato do artefato produzido. Não deve existir pasta física de template com placeholders vazios.
8. **Placeholders obsoletos**: o diff não pode introduzir tokens herdados do scaffold removido
   (nome genérico de cenário, nome genérico de módulo, env vazia de email) ou referências à pasta
   física de template removida.

## Formato de saída

Escreva `tmp/e2e_test/e2e-quality-control.md` com:

```markdown
# Controle de Qualidade E2E

## Resumo

| Pilar | Resultado | Observação |
|---|---|---|
| Configuração | Passou/Ação necessária | ... |
| Estrutura | Passou/Ação necessária | ... |
| Seletores | Passou/Ação necessária | ... |
| Execução | Passou/Ação necessária | ... |
| Contratos de saída | Passou/Ação necessária | ... |

## Achados

- [ ] **Descrição objetiva do problema**
  - Local: `path/to/file.yaml:linha`
  - Antes: `trecho relevante`
  - Depois: `recomendação objetiva`
```

Não altere arquivos de teste durante esta revisão. O relatório deve apontar correções, não aplicá-las.
