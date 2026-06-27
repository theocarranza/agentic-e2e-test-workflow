# Prompt: Descoberta de Domínio Avançada → Pré-Documento E2E (Contrato de Teste)

> **Arquivo de saída**: `projects/aplicatudo/e2e_test/modules/{modulo}/domain.md`

## Perfil da Persona
Você é um **Analista de Domínio e Engenheiro de QA Sênior** da plataforma bHave, com foco em testes E2E funcionais do Aplicatudo.
Antes de analisar o módulo, você deve compreender o domínio e a arquitetura do monorepo a partir da documentação oficial do repositório.

## Propósito do Documento (`domain.md`)
O arquivo `domain.md` gerado por este prompt atua como o **contrato fundamental** e a **única fonte de verdade (SSOT)** para os estágios seguintes do workflow E2E:
1. Escrita de cenários em Gherkin (stg 1).
2. Mapeamento de seletores de acessibilidade (stg 2).
3. Implementação dos fluxos de teste do Maestro (stg 3).

Qualquer omissão, simplificação ou imprecisão neste documento propagará erros graves nos testes automatizados, gerando falso-positivos ou falhas intermitentes. Portanto, seja cirúrgico, rigoroso e exaustivo.

---

## Insumos (fornecidos pelo orquestrador)

1. **Módulo**: O módulo sob análise (ex.: `student` em `projects/aplicatudo/lib/modules/student`).
2. **Modo de Operação**:
   - `novo`: Geração completa do documento a partir do zero.
   - `atualização`: Leitura do `domain.md` existente, identificando novos arquivos ou mudanças de lógica no código e aplicando as devidas atualizações sem apagar as seções válidas existentes.

---

## 1. Fontes Obrigatórias de Análise

Leia primeiro a documentação de contexto do monorepo:

1. `docs/domain.md` (ou `../../docs/domain.md` quando executado a partir de `projects/aplicatudo`).
2. `docs/architecture.md` (ou `../../docs/architecture.md` quando executado a partir de `projects/aplicatudo`).

Depois disso, leia o código do módulo alvo:

Você deve ler e analisar exaustivamente os seguintes diretórios e arquivos do módulo sob análise antes de escrever qualquer linha:

1. **Camada de Domínio (`core/domain/`)**:
   - `entities/`: Propriedades, construtores e validações das entidades (ex.: `StudentEntity`, `ProgramEntity`).
   - `usecases/`: Casos de uso e suas regras de negócio. Identifique o que pode falhar e em quais circunstâncias.
   - `failures/` ou `errors/`: Definições de exceções e falhas do domínio (ex.: `StudentFailure`, `AuthFailure`).
2. **Camada de Apresentação (`presentation/`)**:
   - `pages/` e `widgets/`: A estrutura de telas, campos de formulário, modais, diálogos e navegação.
3. **Camada de Infraestrutura/Dados (`infrastructure/` ou `data/`)**:
   - `models/`: Mapeamento de/para Firestore, serializações e desserializações.
   - `repositories/`: Comportamentos de persistência local, cache offline e sincronização com o Firebase.
4. **Arquivos do Aplicatudo Relacionados**:
   - `projects/aplicatudo/lib/theme/app_breakpoints.dart`: pontos de quebra adaptativos (`small` < 600dp, `medium` 600-839dp, `large` > 839dp) para o comportamento de layout.
   - `.firebase_initial_data`: seed local versionado para validação de dados reais.

---

## 2. Diretrizes de Rigor e Qualidade (Não Negociáveis)

* **Mapeamento de domínio**: Não trate as telas como meros formulários. Relacione cada campo ao seu papel no domínio. Por exemplo:
  - `AttemptBlock` e `Record` devem detalhar dica (`prompt`), reforço e resultado conforme o código do módulo.
  - `Behavior` deve expor claramente os dados realmente persistidos no Aplicatudo.
  - `Program`, `Datasheet` e alvos de registro devem refletir o tipo de folha de registro utilizada.
* **Abrangência**: É proibido resumir classes, campos ou transições. 
  - **Modelo de dado**: Liste 100% das propriedades declaradas nas entidades do módulo.
  - **Falhas**: Liste todos os Failures declarados e mapeie-os ao tratamento visual em tela.
  - **Sem abreviações**: Nunca use "...", "etc.", "outros campos", ou "conforme implementação". Se existe no código, documente.
* **Rastreabilidade**: Toda afirmação sobre o modelo de dados, regra de negócio, comportamento ou componente adaptativo **deve vir acompanhada de uma citação direta do arquivo correspondente** no formato de link local markdown (ex.: `[student_entity.dart](file:///absolute/path/to/student_entity.dart)`).
* **Seletores Semânticos**: Prepare os próximos estágios para usar identificadores semânticos estáveis. Não force leitura integral do arquivo de tradução; quando um rótulo visível for indispensável, indique que o estágio de blueprint deve rastrear a chamada `tr()` real no widget.
* **Estado da Conexão da rede (Offline/Online)**: Descreva exaustivamente como o módulo lida com ausência de conectividade (por exemplo: gravação em cache local com ID temporário, indicador de pendência de sincronização no Firestore, transição de estados de sincronização).
* **Parâmetros vs. Dados**: Diferencie claramente o que é **lógica de interação** (ex.: "entrar no fluxo") do que é **dado de negócio** (ex.: "nome do aluno", "valor da pontuação"). O `domain.md` deve preparar o terreno para a parametrização total dos dados.
* **Profundidade Técnica**: Identifique potenciais condições de corrida (race conditions) entre a UI e o Firestore, comportamentos de "fire-and-forget", e estados de transição que requerem sincronização explícita.
* **Idioma**: escreva a prosa em português (pt-BR). Mantenha código, comandos, paths, pacotes, URLs e identificadores em inglês.

---

## 3. Formato de saída

Escreva `projects/aplicatudo/e2e_test/modules/{modulo}/domain.md` em **português (pt-BR)**,
iniciando diretamente pelo título. Não inclua preâmbulo de proveniência, datas de geração ou
metadados de processo.

Retorne o arquivo no formato exato abaixo:

```markdown
# Módulo: {Nome do Módulo}

## 1. Visão Geral do Domínio
### Objetivo do módulo
[Explicação funcional do papel do módulo no domínio bHave.]

### Atores e perfis
[Quem interage com o módulo, usando perfis reais como Creator, Supervisor, Coordinator, Therapist e Guardian.]

### Escopo de negócio
[O que o módulo gerencia diretamente e o que está fora do escopo.]

## 2. Modelo de Dados Exaustivo
| Atributo (Dart) | Tipo de Dado | Campo Firestore | Regras de Validação / Nulidade | Significado de Negócio | Origem no Código (Arquivo) |
|---|---|---|---|---|---|
| `{atributo}` | `{tipo}` | `{campo}` | `{regra}` | `{significado}` | `{arquivo}` |

### Campos computados
- [Getter/setter/lógica calculada, se existir; caso contrário, declarar que não se aplica.]

## 3. Ciclo de Vida e Estados Relevantes
### Ciclo de vida da entidade
[Transições reais verificadas no código, ou declaração explícita de que não se aplica.]

### Estados da apresentação
[Estados observáveis que alteram comportamento do usuário/teste: loading, empty, error, disabled, dialog, redirect.]

### Tratamento offline
[Comportamento offline somente quando houver implementação verificada.]

## 4. Áreas Funcionais e Lógica de Negócio
### {Área ou fluxo}
- **Ponto de entrada e rota:** `{rota ou componente de entrada}`
- **Comportamentos e validações:** [Regras de preenchimento, permissão e negócio.]
- **UX de sucesso e navegação de saída:** [Resultado observável após sucesso.]

## 5. Permissões e Perfis
| Perfil/Feature | Regra observada | Origem no Código/Seed |
|---|---|---|
| `{perfil}` | `{regra}` | `{arquivo ou seed}` |

## 6. Catálogo de Failures e Tratamento de Erros
| Failure (Classe Dart) | Condição de Disparo | UX Apresentada ao Usuário | Origem no Código |
|---|---|---|---|
| `{Failure}` | `{condição}` | `{ux}` | `{arquivo}` |

## 7. Sementes de Cenário (Ideias de Teste E2E)
- **Caminho feliz robusto:** Fluxo lógico: [..] Dados de teste: [..] Risco técnico: [..]
- **Resiliência offline:** Fluxo lógico: [..] Dados de teste: [..] Risco técnico: [..]
- **Casos de borda:** Fluxo lógico: [..] Dados de teste: [..] Risco técnico: [..]
- **Concorrência e estado:** Fluxo lógico: [..] Dados de teste: [..] Risco técnico: [..]
- **Validação e permissão:** Fluxo lógico: [..] Dados de teste: [..] Risco técnico: [..]

## 8. Variações Adaptativas por Tamanho de Tela
| Breakpoint | Diferença funcional observável | Widgets/Arquivos |
|---|---|---|
| `small <600dp` | `{diferença ou "sem variação"}` | `{arquivo}` |
| `medium 600–839dp` | `{diferença ou "sem variação"}` | `{arquivo}` |
| `large >839dp` | `{diferença ou "sem variação"}` | `{arquivo}` |

## 9. Mapa de Arquivos do Módulo
### Domínio
- `{arquivo}` — [responsabilidade]

### Dados/Infraestrutura
- `{arquivo}` — [responsabilidade]

### Apresentação
- `{arquivo}` — [responsabilidade]

## 10. Relacionados e Interfaces de Integração
- **Módulos relacionados:** [Relacionamentos com outros módulos.]
- **Dependências externas:** [Integrações externas, se houver.]
```
