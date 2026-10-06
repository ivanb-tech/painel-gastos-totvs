# Painel de gastos TOTVS

Painel de uma página que mostra para a diretoria **quanto a empresa paga à TOTVS, por serviço e mês a mês**, a partir da **Ficha de Faturamento** exportada do TOTVS Protheus (`.xlsx`).

**Para atualizar o painel, basta colocar a ficha nova na pasta [`data/`](data/).** O GitHub gera o painel de novo e publica no GitHub Pages sozinho, sem precisar programar nada.

**Painel publicado (dados fictícios):** https://ivanb-tech.github.io/painel-gastos-totvs/

> ⚠️ **Os dados deste repositório são fictícios** (cliente "EMPRESA EXEMPLO LTDA"). Este repositório é **público**, e o painel publicado no GitHub Pages também. **Não envie fichas reais para cá.** Para usar com dados reais, veja [Usando com dados reais](#usando-com-dados-reais).

---

## O que o painel mostra

| Bloco | O que responde |
|---|---|
| **Indicadores** | Total faturado no período, mensalidade recorrente atual e quanto ela variou desde o 1º mês, projeção anual, média mensal e serviço de maior peso |
| **Faturamento mensal por grupo** | Barras empilhadas por mês de **emissão da NF**, divididas por grupo de serviço (ERP, AMS, Cloud, Comex…) |
| **Quanto custa cada serviço** | Ranking pela **descrição** do serviço, com o total no período e quanto ele pesa no gasto |
| **Mês a mês por serviço** | Tabela serviço × mês com o **valor total do serviço**. Os meses com reajuste ficam sublinhados |
| **Por que a mensalidade subiu** | Divide o aumento da mensalidade entre **reajustes de preço** e **serviços novos** |
| **Reajustes aplicados** | Mês, serviço, quanto subiu em R$/mês e em % |
| **Destaques** | Frases geradas automaticamente: concentração do gasto, picos por setup, serviços novos ou renomeados e mês ainda parcial |

Passando o mouse sobre as barras e as células aparecem detalhes: NF, quantidade × preço unitário e vencimento. O painel tem tema claro e escuro e cabe em **uma folha A4 deitada** ao imprimir ou salvar em PDF.

---

## Como atualizar com uma ficha nova (sem programar)

1. No Protheus, exporte a **Ficha de Faturamento** para `.xlsx`, do jeito de sempre.
2. No GitHub, abra a pasta [`data/`](data/) → **Add file** → **Upload files** → arraste a planilha → **Commit changes**.
3. Aguarde 1 a 2 minutos. Dá para acompanhar na aba **Actions** (fluxo "Atualizar painel").
4. Abra o painel em `https://<usuário>.github.io/painel-gastos-totvs/`. O link também aparece em **Settings → Pages**.

**Algumas regras para as fichas:**

- **Todas** as planilhas `.xlsx` da pasta `data/` entram no painel. Você pode ter uma ficha por mês ou uma ficha com o ano inteiro.
- Se a mesma NF aparecer em mais de uma ficha, ela é contada **uma vez só** (o script compara NF + produto + descrição + emissão + valor).
- Para substituir uma ficha por uma versão mais nova, apague a antiga ou envie a nova com o **mesmo nome**.
- Se o último mês ainda estiver incompleto, o painel marca esse mês com `*` e usa o mês anterior como mensalidade de referência.

### Formato esperado da planilha

É a ficha padrão do Protheus. O script procura a linha de cabeçalho em qualquer posição da planilha e ignora o título `FICHA_FATURAMENTO` que vem antes dela.

| Coluna | Uso | Obrigatória |
|---|---|---|
| `DESCRICAO` | Nome do serviço (é o que agrupa tudo) | ✅ |
| `VAL_TOTAL` | Valor total do item, que é o valor somado no painel | ✅ |
| `EMISSAO` | Data de emissão da NF, que define o mês | ✅ |
| `VAL_UNIT`, `QUANT` | Detectar reajustes e mostrar o detalhe | recomendada |
| `PRODUTO` | Reconhecer serviço renomeado (mesmo código com outra descrição) | recomendada |
| `NF_ELETR`, `VENCTO` | Detalhe na dica do mouse e remoção de duplicados | recomendada |
| `NOME_CLIEN`, `CONTRATO` | Subtítulo do painel | opcional |
| `VAL_BOLETO` | Lido, mas não é somado (o valor do boleto vem com os impostos retidos descontados) | opcional |

Os valores podem vir como texto no formato brasileiro (`16.032,20`) ou como número. As datas podem vir como texto `dd/mm/aaaa` ou como data do Excel.

---

## Grupos de serviço

Os grupos ficam em [`config/servicos.json`](config/servicos.json):

```json
{
  "titulo": "Gastos com TOTVS",
  "regex_servicos_pontuais": "SETUP|IMPLANTA",
  "grupos": [
    { "chave": "erp", "nome": "ERP TOTVS Intera (licenças)",
      "servicos": ["INTERA BACKOFFICE COMPLETO", "TOTVS INTERA MANUFATURA"] }
  ]
}
```

- **`servicos`**: lista das descrições exatamente como aparecem na coluna `DESCRICAO`. Maiúsculas e minúsculas não fazem diferença.
- **Serviço que não está em nenhum grupo** aparece em **"Outros"**. O fluxo do GitHub também lista esses serviços no resumo da execução (aba Actions → execução → *Summary*), para você incluir o serviço no grupo certo.
- **`regex_servicos_pontuais`**: descrições que combinam com esse padrão são tratadas como **custo pontual** (setup, implantação). Elas entram no total, mas ficam fora da mensalidade recorrente.
- A ordem dos grupos define as cores. São no máximo 8 cores, e a paleta foi validada para daltonismo.

---

## Rodar no seu computador

Precisa de Python 3.9 ou superior.

```bash
pip install -r requirements.txt
python scripts/build.py                         # lê data/ e gera dist/index.html
python scripts/build.py --data C:/fichas --out painel.html   # outra pasta/arquivo
```

O resultado é **um único arquivo HTML**, sem nenhuma dependência externa. Dá para abrir no navegador, mandar por e-mail, salvar em PDF ou publicar como artefato.

---

## Usando com dados reais

Fichas reais têm contrato, NFs e valores pagos. **Não as coloque em repositório público.** Há duas formas seguras:

1. **Só no seu computador:** clone o repositório, coloque as fichas reais em outra pasta e rode `python scripts/build.py --data <pasta> --out painel.html`. Nada vai para a internet.
2. **Repositório privado:** faça uma cópia privada (**Use this template** ou fork privado), troque o exemplo em `data/` pelas fichas reais e use o mesmo fluxo automático. Atenção: no plano gratuito do GitHub, o Pages de repositório privado não fica disponível ou fica **público**. Nesse caso, baixe o HTML gerado em *Actions → Artifacts* em vez de usar o Pages.

---

## Estrutura

```
data/                 fichas .xlsx (entrada) — aqui só a de exemplo
config/servicos.json  grupos de serviço, título, regra de custo pontual
template/painel.html  layout, gráficos e cálculos (HTML + JS puro, sem bibliotecas)
scripts/build.py      lê as fichas, junta, remove duplicados e injeta no template
.github/workflows/    fluxo que gera e publica no GitHub Pages
```

### Como os números são calculados

- **Mês:** mês da data de **emissão** da NF.
- **Mensalidade recorrente:** soma do mês sem os serviços pontuais. Se o último mês estiver parcial (faltam serviços que vieram no mês anterior), a referência passa a ser o mês anterior.
- **Reajuste:** mudança no `VAL_UNIT` de um serviço de um mês para o seguinte.
- **Serviço novo:** aparece no mês de referência e não existia no 1º mês. Se tiver o mesmo `PRODUTO` de um serviço antigo, é tratado como **renomeado**, e a diferença de valor conta como reajuste.

## Licença

MIT
