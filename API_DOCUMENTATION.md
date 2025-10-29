# Marketplace API Documentation

## Índice
- [Visão Geral](#visão-geral)
- [Autenticação](#autenticação)
- [Endpoints](#endpoints)
  - [Auth](#auth-endpoints)
  - [Products](#products-endpoints)
- [Modelos de Dados](#modelos-de-dados)
- [Códigos de Status HTTP](#códigos-de-status-http)
- [Fluxos de Uso](#fluxos-de-uso)
- [Questão Situacional](#questão-situacional)

---

## Visão Geral

**Framework:** Flask com arquitetura baseada em Blueprints
**Banco de Dados:** MongoDB (usando MongoEngine ODM)
**Autenticação:** JWT (JSON Web Tokens) via Flask-JWT-Extended
**URL Base:** `http://localhost:5000` (desenvolvimento)

---

## Autenticação

### Como Autenticar

1. Registre um usuário usando `POST /auth/register`
2. Faça login usando `POST /auth/login` para obter um token JWT
3. Inclua o token no header `Authorization` para rotas protegidas:

```
Authorization: Bearer <seu_token_jwt>
```

### Rotas Públicas (sem autenticação)
- `POST /auth/register`
- `POST /auth/login`
- `GET /products`
- `GET /products/<product_id>`

### Rotas Protegidas (requerem autenticação)
- `GET /auth/me`
- `POST /products`
- `POST /products/<product_id>/images`
- `POST /products/<product_id>/generate-code`
- `POST /products/confirm-with-code`

---

## Endpoints

### Auth Endpoints

#### 1. Registrar Usuário
```http
POST /auth/register
```

**Descrição:** Cria uma nova conta de usuário no sistema.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "usuario@exemplo.com",
  "name": "Nome do Usuário",
  "password": "senhaSegura123",
  "cellphone": "+5511999999999"
}
```

**Validações:**
- `email`: Obrigatório, deve ser um email válido e único
- `name`: Obrigatório
- `password`: Obrigatório
- `cellphone`: Obrigatório

**Response (201 Created):**
```json
{
  "message": "usuário criado",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "usuario@exemplo.com",
    "name": "Nome do Usuário",
    "cellphone": "+5511999999999",
    "created_at": "2025-01-15T10:30:00.000Z"
  }
}
```

**Possíveis Erros:**
- `400 Bad Request`: Email, password ou cellphone faltando, ou email inválido
- `409 Conflict`: Email já cadastrado

---

#### 2. Login
```http
POST /auth/login
```

**Descrição:** Autentica o usuário e retorna um token JWT.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "senhaSegura123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Possíveis Erros:**
- `400 Bad Request`: Email ou password faltando
- `401 Unauthorized`: Credenciais inválidas

---

#### 3. Obter Perfil do Usuário Atual
```http
GET /auth/me
```

**Descrição:** Retorna as informações do usuário autenticado.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "usuario@exemplo.com",
  "name": "Nome do Usuário",
  "cellphone": "+5511999999999",
  "created_at": "2025-01-15T10:30:00.000Z"
}
```

**Possíveis Erros:**
- `401 Unauthorized`: Token ausente ou inválido
- `422 Unprocessable Entity`: Formato do token JWT inválido

---

### Products Endpoints

#### 1. Listar Produtos Disponíveis
```http
GET /products
```

**Descrição:** Lista todos os produtos que ainda não foram vendidos.

**Query Parameters:**
- `q` (opcional): Busca por termo no título ou descrição (case-insensitive)

**Exemplos:**
```
GET /products
GET /products?q=iPhone
GET /products?q=notebook
```

**Response (200 OK):**
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "title": "iPhone 13 Pro",
    "description": "256GB, azul",
    "price": 3500.00,
    "category": "eletrônicos",
    "estado_de_conservacao": "seminovo",
    "em_destaque": false,
    "owner": {
      "id": "507f1f77bcf86cd799439012",
      "email": "vendedor@exemplo.com",
      "name": "João Silva",
      "cellphone": "+5511999999999",
      "created_at": "2025-01-14T08:00:00.000Z"
    },
    "buyer": null,
    "images": [
      "https://res.cloudinary.com/dgxv5exvc/image/upload/v1234567890/marketplace/products/507f1f77bcf86cd799439011/photo1.jpg"
    ],
    "thumbnail": "https://res.cloudinary.com/dgxv5exvc/image/upload/v1234567890/marketplace/products/507f1f77bcf86cd799439011/photo1.jpg",
    "created_at": "2025-01-15T10:30:00.000Z"
  },
  {
    "id": "507f1f77bcf86cd799439013",
    "title": "Notebook Dell",
    "description": "i7, 16GB RAM, SSD 512GB",
    "price": 2800.00,
    "category": "eletrônicos",
    "estado_de_conservacao": "usado",
    "em_destaque": false,
    "owner": {
      "id": "507f1f77bcf86cd799439014",
      "email": "maria@exemplo.com",
      "name": "Maria Santos",
      "cellphone": "+5511988888888",
      "created_at": "2025-01-13T15:30:00.000Z"
    },
    "buyer": null,
    "images": [],
    "thumbnail": null,
    "created_at": "2025-01-15T09:20:00.000Z"
  }
]
```

**Observações:**
- Retorna apenas produtos onde `buyer` é `null` (produtos ainda não vendidos)
- Ordenados por data de criação (mais recentes primeiro)
- Busca é case-insensitive e busca substring
- Retorna informações completas do owner (incluindo email e cellphone)

---

#### 2. Criar Produto
```http
POST /products
```

**Descrição:** Cria um novo produto para venda (requer autenticação).

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "iPhone 13 Pro",
  "description": "256GB, azul",
  "price": 3500.00,
  "category": "eletrônicos",
  "estado_de_conservacao": "seminovo"
}
```

**Validações:**
- `title`: Obrigatório, máximo 200 caracteres
- `description`: Opcional (default: string vazia)
- `price`: Obrigatório, deve ser >= 0
- `category`: Obrigatório, valores permitidos: "eletrodomésticos", "eletrônicos", "móveis", "outros"
- `estado_de_conservacao`: Obrigatório, valores permitidos: "novo", "seminovo", "usado"

**Response (201 Created):**
```json
{
  "message": "produto criado",
  "product": {
    "id": "507f1f77bcf86cd799439011",
    "title": "iPhone 13 Pro",
    "description": "256GB, azul",
    "price": 3500.00,
    "category": "eletrônicos",
    "estado_de_conservacao": "seminovo",
    "em_destaque": false,
    "owner": {
      "id": "507f1f77bcf86cd799439012",
      "email": "vendedor@exemplo.com",
      "name": "João Silva",
      "cellphone": "+5511999999999",
      "created_at": "2025-01-14T08:00:00.000Z"
    },
    "buyer": null,
    "images": [],
    "thumbnail": null,
    "created_at": "2025-01-15T10:30:00.000Z"
  }
}
```

**Possíveis Erros:**
- `400 Bad Request`: Campos obrigatórios faltando (title, price, category, estado_de_conservacao), preço negativo, valores inválidos de category ou estado_de_conservacao
- `401 Unauthorized`: Token ausente ou inválido
- `404 Not Found`: Usuário autenticado não existe no banco

---

#### 3. Adicionar Imagem ao Produto
```http
POST /products/<product_id>/images
```

**Descrição:** Adiciona uma imagem ao produto via Cloudinary (requer autenticação).

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**URL Parameters:**
- `product_id`: ID do produto

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
}
```

**Validações:**
- `image`: Obrigatório, string base64 da imagem ou URL da imagem
- Apenas o owner pode adicionar imagens
- Imagens são enviadas para o Cloudinary e otimizadas automaticamente

**Response (201 Created):**
```json
{
  "message": "imagem adicionada com sucesso",
  "image_url": "https://res.cloudinary.com/dgxv5exvc/image/upload/v1234567890/marketplace/products/507f1f77bcf86cd799439011/abc123.jpg",
  "product": {
    "id": "507f1f77bcf86cd799439011",
    "title": "iPhone 13 Pro",
    "description": "Seminovo, 256GB, azul",
    "price": 3500.00,
    "owner": {
      "id": "507f1f77bcf86cd799439012",
      "email": "vendedor@exemplo.com",
      "name": "João Silva",
      "cellphone": "+5511999999999",
      "created_at": "2025-01-14T08:00:00.000Z"
    },
    "buyer": null,
    "images": [
      "https://res.cloudinary.com/dgxv5exvc/image/upload/v1234567890/marketplace/products/507f1f77bcf86cd799439011/abc123.jpg"
    ],
    "thumbnail": "https://res.cloudinary.com/dgxv5exvc/image/upload/v1234567890/marketplace/products/507f1f77bcf86cd799439011/abc123.jpg",
    "created_at": "2025-01-15T10:30:00.000Z"
  }
}
```

**Possíveis Erros:**
- `400 Bad Request`: Imagem faltando ou formato inválido
- `401 Unauthorized`: Token ausente ou inválido
- `403 Forbidden`: Usuário não é o dono do produto
- `404 Not Found`: Produto não encontrado
- `500 Internal Server Error`: Erro ao fazer upload da imagem no Cloudinary

**Observações:**
- Imagens são armazenadas no Cloudinary e otimizadas automaticamente
- O campo `thumbnail` sempre retorna a primeira imagem da lista
- É possível adicionar múltiplas imagens fazendo múltiplas requisições
- Imagens são organizadas em pastas por produto no Cloudinary

---

#### 4. Obter Detalhes de um Produto
```http
GET /products/<product_id>
```

**Descrição:** Retorna informações detalhadas de um produto específico.

**URL Parameters:**
- `product_id`: ID do produto (formato MongoDB ObjectId)

**Exemplo:**
```
GET /products/507f1f77bcf86cd799439011
```

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "title": "iPhone 13 Pro",
  "description": "256GB, azul",
  "price": 3500.00,
  "category": "eletrônicos",
  "estado_de_conservacao": "seminovo",
  "em_destaque": false,
  "owner": {
    "id": "507f1f77bcf86cd799439012",
    "email": "vendedor@exemplo.com",
    "name": "João Silva",
    "cellphone": "+5511999999999",
    "created_at": "2025-01-14T08:00:00.000Z"
  },
  "buyer": null,
  "images": [
    "https://res.cloudinary.com/dgxv5exvc/image/upload/v1234567890/marketplace/products/507f1f77bcf86cd799439011/photo1.jpg",
    "https://res.cloudinary.com/dgxv5exvc/image/upload/v1234567890/marketplace/products/507f1f77bcf86cd799439011/photo2.jpg"
  ],
  "thumbnail": "https://res.cloudinary.com/dgxv5exvc/image/upload/v1234567890/marketplace/products/507f1f77bcf86cd799439011/photo1.jpg",
  "created_at": "2025-01-15T10:30:00.000Z"
}
```

**Observações:**
- Retorna informações completas do owner e buyer (se houver)
- Útil para obter o cellphone do vendedor para contato via WhatsApp
- Campo `images` contém todas as URLs das imagens do produto
- Campo `thumbnail` é a primeira imagem (usado para exibição em miniatura na listagem)

**Possíveis Erros:**
- `400 Bad Request`: Formato de ID inválido
- `404 Not Found`: Produto não encontrado

---

#### 5. Gerar Código de Confirmação
```http
POST /products/<product_id>/generate-code
```

**Descrição:** Gera um código de confirmação de 8 caracteres para o produto. Apenas o dono do produto pode gerar o código.

**Headers:**
```
Authorization: Bearer <access_token>
```

**URL Parameters:**
- `product_id`: ID do produto

**Response - Primeira Geração (201 Created):**
```json
{
  "message": "código gerado com sucesso. Envie este código para o comprador pelo WhatsApp!",
  "confirmation_code": "ABC12345",
  "product": {
    "id": "507f1f77bcf86cd799439011",
    "title": "iPhone 13 Pro",
    "description": "Seminovo, 256GB, azul",
    "price": 3500.00,
    "owner": {
      "id": "507f1f77bcf86cd799439012",
      "email": "vendedor@exemplo.com",
      "name": "João Silva",
      "cellphone": "+5511999999999",
      "created_at": "2025-01-14T08:00:00.000Z"
    },
    "buyer": null,
    "created_at": "2025-01-15T10:30:00.000Z"
  }
}
```

**Response - Código Já Existe (200 OK):**
```json
{
  "message": "código já existe",
  "confirmation_code": "ABC12345"
}
```

**Possíveis Erros:**
- `400 Bad Request`: Formato de ID inválido
- `401 Unauthorized`: Token ausente ou inválido
- `403 Forbidden`: Usuário não é o dono do produto
- `404 Not Found`: Produto não encontrado

**Observações:**
- Código tem 8 caracteres (letras, números, URL-safe)
- Código é único no sistema
- Se já existe código, retorna o existente

---

#### 6. Confirmar Compra com Código
```http
POST /products/confirm-with-code
```

**Descrição:** Confirma a compra de um produto usando o código fornecido pelo vendedor.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "confirmation_code": "ABC12345"
}
```

**Response (200 OK):**
```json
{
  "message": "compra confirmada com sucesso!",
  "product": {
    "id": "507f1f77bcf86cd799439011",
    "title": "iPhone 13 Pro",
    "description": "Seminovo, 256GB, azul",
    "price": 3500.00,
    "owner": {
      "id": "507f1f77bcf86cd799439012",
      "email": "vendedor@exemplo.com",
      "name": "João Silva",
      "cellphone": "+5511999999999",
      "created_at": "2025-01-14T08:00:00.000Z"
    },
    "buyer": {
      "id": "507f1f77bcf86cd799439015",
      "email": "comprador@exemplo.com",
      "name": "Ana Costa",
      "cellphone": "+5511977777777",
      "created_at": "2025-01-15T09:00:00.000Z"
    },
    "created_at": "2025-01-15T10:30:00.000Z"
  }
}
```

**Possíveis Erros:**
- `400 Bad Request`:
  - Código de confirmação faltando
  - Formato de código inválido
  - Usuário é o dono tentando confirmar próprio produto
  - Produto já confirmado por outro comprador
- `401 Unauthorized`: Token ausente ou inválido
- `404 Not Found`: Código não encontrado

**Regras de Negócio:**
- Apenas um comprador por produto
- Dono não pode confirmar próprio produto
- Primeiro a confirmar com código válido ganha o produto
- Após confirmação, produto não aparece mais na lista pública

---

## Modelos de Dados

### User Model

**Collection:** `users`

```typescript
{
  id: ObjectId,              // Identificador único
  email: string,             // Email único, indexado
  name: string,              // Nome do usuário (max 120 chars)
  password_hash: string,     // Senha com hash
  cellphone: string,         // Telefone celular (obrigatório)
  created_at: DateTime       // Data de criação da conta
}
```

**Métodos:**
- `set_password(password)`: Faz hash e armazena a senha
- `check_password(password)`: Verifica a senha
- `to_dict()`: Retorna dicionário JSON-serializável

---

### Product Model

**Collection:** `products`

```typescript
{
  id: ObjectId,                    // Identificador único
  title: string,                   // Nome do produto (max 200 chars)
  description: string,             // Descrição do produto
  price: float,                    // Preço (>= 0)
  category: string,                // Categoria: "eletrodomésticos", "eletrônicos", "móveis", "outros"
  estado_de_conservacao: string,   // Estado: "novo", "seminovo", "usado"
  em_destaque: boolean,            // Indica se é anúncio em destaque (padrão: false)
  owner: User,                     // Objeto User completo do vendedor
  buyer: User | null,              // Objeto User completo do comprador (nullable)
  confirmation_code: string,       // Código único de 8 caracteres (sparse/nullable)
  images: string[],                // Lista de URLs das imagens no Cloudinary
  thumbnail: string | null,        // URL da primeira imagem (para exibição na listagem)
  created_at: DateTime             // Data de criação
}
```

**Observações:**
- No banco de dados, `owner` e `buyer` são referências (ObjectId)
- Na serialização (`to_dict()`), são retornados como objetos User completos incluindo email, name, cellphone
- Isso facilita o contato entre vendedor e comprador via WhatsApp
- O campo `images` armazena URLs das imagens hospedadas no Cloudinary
- O campo `thumbnail` é gerado automaticamente e sempre aponta para a primeira imagem da lista (ou null se não houver imagens)
- Imagens são otimizadas automaticamente pelo Cloudinary
- O campo `category` é obrigatório e aceita apenas: "eletrodomésticos", "eletrônicos", "móveis", "outros"
- O campo `estado_de_conservacao` é obrigatório e aceita apenas: "novo", "seminovo", "usado"
- O campo `em_destaque` é um boolean (padrão false) preparado para futura funcionalidade de anúncios pagos

**Métodos:**
- `to_dict()`: Retorna dicionário JSON-serializável com todos os campos incluindo owner e buyer expandidos

**Índices:** `owner`, `buyer`, `confirmation_code`, `category`, `em_destaque`

---

## Códigos de Status HTTP

| Código | Significado | Causas Comuns |
|--------|-------------|---------------|
| 200 | OK | GET bem-sucedido, código já existe |
| 201 | Created | Registro, criação de produto, primeira geração de código |
| 400 | Bad Request | Input inválido, campos obrigatórios faltando, violação de regras de negócio |
| 401 | Unauthorized | Token JWT ausente ou inválido |
| 403 | Forbidden | Usuário sem permissão (ex: não é dono do produto) |
| 404 | Not Found | Recurso não existe (usuário, produto ou código) |
| 409 | Conflict | Email duplicado no registro |
| 422 | Unprocessable Entity | Formato de token JWT inválido |

---

## Fluxos de Uso

### Fluxo 1: Registro e Criação de Produto

```
1. POST /auth/register
   → Criar conta

2. POST /auth/login
   → Obter token JWT

3. POST /products
   → Criar produto (usando token do passo 2)

4. GET /products
   → Ver produto na lista pública
```

---

### Fluxo 2: Processo Completo de Venda

```
VENDEDOR:
1. POST /auth/login
   → Fazer login

2. POST /products
   → Criar produto para venda

3. POST /products/<product_id>/generate-code
   → Gerar código (ex: "ABC12345")

4. [Via WhatsApp/Chat]
   → Enviar código para o comprador

COMPRADOR:
5. POST /auth/login
   → Fazer login

6. POST /products/confirm-with-code
   Body: { "confirmation_code": "ABC12345" }
   → Confirmar compra com código

RESULTADO:
7. GET /products
   → Produto não aparece mais na lista (pois tem buyer preenchido)

8. GET /products/<product_id>
   → Produto agora mostra objeto buyer completo com informações do comprador
   → Vendedor e comprador podem trocar contatos via cellphone para finalizar negociação
```

---

## Questão Situacional

### Cenário de Implementação Frontend

**Situação:**
Você é o desenvolvedor frontend responsável por implementar a tela de "Meus Produtos" onde o vendedor pode visualizar todos os seus produtos listados e gerenciar os códigos de confirmação.

**Requisitos da Tela:**
1. Mostrar lista de produtos criados pelo usuário logado
2. Para cada produto, mostrar: título, preço, descrição, status (disponível/vendido)
3. Botão "Gerar Código" para produtos disponíveis
4. Exibir código gerado em formato copiável
5. Indicar visualmente quando produto foi vendido (mostrar comprador)

**Perguntas:**

1. **Quais endpoints você precisará chamar para implementar esta tela?**
   - Liste os endpoints necessários
   - Explique a ordem e momento de cada chamada

2. **Atualmente a API não possui um endpoint específico para listar "meus produtos". Como você resolveria isso no frontend usando os endpoints existentes?**
   - Descreva a solução
   - Quais são as limitações desta abordagem?
   - Que endpoint você sugeriria adicionar à API?

3. **Implemente a lógica de geração e exibição do código:**
   ```javascript
   // Complete a função abaixo
   async function handleGenerateCode(productId) {
     // Seu código aqui
     // Considere:
     // - Tratamento de erro
     // - Caso onde código já existe
     // - Feedback visual ao usuário
   }
   ```

4. **Como você implementaria a atualização em tempo real do status de "vendido" quando um comprador confirmar a compra?**
   - Polling? WebSocket? Outra solução?
   - Justifique sua escolha considerando os recursos atuais da API

5. **Tratamento de Erros:**
   Liste 3 cenários de erro que podem ocorrer ao gerar um código e como você exibiria isso para o usuário.

---

### Resposta Esperada (Exemplo)

<details>
<summary>Clique para ver resposta modelo</summary>

**1. Endpoints necessários:**
```
- GET /auth/me (ao carregar a página, para confirmar autenticação)
- GET /products (para obter todos produtos)
- POST /products/<id>/generate-code (ao clicar em "Gerar Código")
- GET /products/<id> (opcional, para refresh de produto específico)
```

**2. Solução para filtrar "meus produtos":**
```javascript
// Obter produtos e filtrar pelo owner.id do usuário atual
const currentUser = await fetch('/auth/me');
const userData = await currentUser.json();

const allProducts = await fetch('/products');
const productsData = await allProducts.json();

// Limitação: isso só retorna produtos NÃO vendidos
const myAvailableProducts = productsData.filter(
  p => p.owner.id === userData.id
);

// Problema: não consigo ver produtos que já vendi!
```

**Endpoint sugerido:**
```
GET /products/my-products
- Retorna todos produtos do usuário (vendidos e disponíveis)
- Requer autenticação
```

**3. Implementação:**
```javascript
async function handleGenerateCode(productId) {
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(
      `/products/${productId}/generate-code`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    if (!response.ok) {
      if (response.status === 403) {
        showError('Você não é o dono deste produto');
      } else if (response.status === 404) {
        showError('Produto não encontrado');
      } else {
        showError('Erro ao gerar código');
      }
      return;
    }

    const data = await response.json();

    // Código já existia ou foi gerado
    displayCode(data.confirmation_code);

    if (response.status === 201) {
      showSuccess('Código gerado! Envie para o comprador.');
    } else {
      showInfo('Código já existe para este produto.');
    }

    // Copiar para clipboard
    navigator.clipboard.writeText(data.confirmation_code);

  } catch (error) {
    showError('Erro de conexão. Tente novamente.');
  }
}
```

**4. Atualização em tempo real:**

Dado que a API não possui WebSocket, a melhor abordagem é:
```javascript
// Polling simples a cada 10 segundos na tela "Meus Produtos"
setInterval(async () => {
  await refreshMyProducts();
}, 10000);
```

Justificativa: Polling é suficiente para este caso de uso, pois vendas não acontecem com alta frequência. WebSocket seria melhor mas requer mudanças no backend.

**5. Cenários de erro:**
- **403 Forbidden**: "Você não tem permissão para gerar código deste produto" (toast vermelho)
- **401 Unauthorized**: Redirecionar para login com mensagem "Sessão expirada"
- **Network Error**: "Erro de conexão. Verifique sua internet e tente novamente" (toast com botão retry)

</details>

---

## Configuração do Ambiente

### Variáveis de Ambiente Necessárias

Crie um arquivo `.env` com:

```bash
MONGO_URI=mongodb://localhost:27017/marketplace
JWT_SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=development
JWT_ALGORITHM=HS256

# Cloudinary (para upload de imagens)
CLOUDINARY_CLOUD_NAME=seu-cloud-name
CLOUDINARY_API_KEY=sua-api-key
CLOUDINARY_API_SECRET=seu-api-secret
```

**Como obter as credenciais do Cloudinary:**
1. Crie uma conta gratuita em https://cloudinary.com
2. No dashboard, copie o Cloud Name, API Key e API Secret
3. Adicione as variáveis no arquivo `.env`

---

## Executando Testes

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar todos os testes
pytest tests/

# Executar testes específicos
pytest tests/test_auth.py
pytest tests/test_products.py

# Com coverage
pytest --cov=app tests/
```

**Cobertura de Testes:**
- **Auth:** 12 testes cobrindo registro, login, perfil
- **Products:** 25 testes cobrindo CRUD, busca, geração de código, confirmação

---

## Regras de Negócio Importantes

1. ✅ **Disponibilidade:** Apenas produtos sem comprador aparecem em `/products`
2. ✅ **Geração de Código:** Somente dono pode gerar código
3. ✅ **Confirmação:** Primeiro comprador a confirmar com código válido ganha
4. ❌ **Restrição de Dono:** Dono não pode confirmar próprio produto
5. 🔍 **Busca:** Case-insensitive, busca substring em título e descrição
6. 💰 **Validação de Preço:** Aceita apenas valores >= 0
7. 🔐 **Autenticação:** Todas as ações de modificação requerem JWT válido
8. 🎫 **Código Único:** Códigos de confirmação são únicos no sistema

---

## Contato e Suporte

Para dúvidas sobre a API, consulte:
- Repositório: [Link do repositório]
- Testes: `tests/test_auth.py` e `tests/test_products.py`
- Código fonte: `app/routes/auth.py` e `app/routes/products.py`

---

**Versão:** 1.3
**Última Atualização:** Janeiro 2025

**Changelog:**
- v1.3 (Janeiro 2025):
  - Adicionado campo `category` obrigatório (valores: "eletrodomésticos", "eletrônicos", "móveis", "outros")
  - Adicionado campo `estado_de_conservacao` obrigatório (valores: "novo", "seminovo", "usado")
  - Adicionado campo `em_destaque` (boolean, padrão false) preparado para anúncios pagos
  - Novos índices para `category` e `em_destaque` para melhor performance
  - Validação automática de valores permitidos para category e estado_de_conservacao
- v1.2 (Janeiro 2025):
  - Integração com Cloudinary para upload de imagens
  - Novo endpoint `POST /products/<product_id>/images` para adicionar imagens
  - Campos `images` e `thumbnail` adicionados ao modelo Product
  - Imagens otimizadas automaticamente pelo Cloudinary
  - Suporte para múltiplas imagens por produto
- v1.1 (Janeiro 2025):
  - Campo `cellphone` adicionado ao User (obrigatório)
  - Campo `cellphone` obrigatório no registro
  - Endpoints de produtos agora retornam objetos completos de owner e buyer (incluindo cellphone)
  - Modelo Cellphone removido (simplificado como atributo do User)
- v1.0 (Janeiro 2025):
  - Versão inicial da API
