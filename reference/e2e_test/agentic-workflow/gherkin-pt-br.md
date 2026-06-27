# Palavras-chave Gherkin — português (pt-BR)

Use estas palavras-chave ao escrever planos de teste em Gherkin para este projeto.
O idioma padrão do projeto é **pt-BR**; nunca use as palavras-chave em inglês no artefato final.

| Estrutura | Palavra-chave em inglês | Palavras-chave em pt-BR |
| --- | --- | --- |
| Feature | Feature | `Funcionalidade` |
| Rule | Rule | `Regra` |
| Background | Background | `Contexto` |
| Scenario | Scenario | `Cenário` |
| Scenario Outline | Scenario Outline | `Esquema do Cenário` |
| Examples | Examples | `Exemplos` |
| Given | Given | `Dado` / `Dada` / `Dados` / `Dadas` |
| When | When | `Quando` |
| Then | Then | `Então` |
| And | And | `E` |
| But | But | `Mas` |

## Regras de uso

- Use `Dado`/`Dada`/`Dados`/`Dadas` conforme o gênero e número do sujeito da frase.
- `E` e `Mas` herdam o tipo do passo anterior (Given/When/Then) — use-os para encadear passos sem repetir a palavra-chave principal.
- O bloco `Contexto` contém apenas passos `Dado`/`E` que se aplicam a **todos** os cenários do arquivo.
- Tags (`@small`, `@medium`, `@large`, `@android`) são sempre em inglês e sem acento.
