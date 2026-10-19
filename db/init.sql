CREATE TABLE IF NOT EXISTS itens (
    id         SERIAL PRIMARY KEY,
    descricao  VARCHAR(200) NOT NULL,
    local      VARCHAR(100) NOT NULL,
    foto       VARCHAR(100),
    criado_em  TIMESTAMP NOT NULL DEFAULT NOW()
);
INSERT INTO itens (descricao, local) VALUES
    ('Garrafa termica azul', 'Biblioteca'),
    ('Carregador de notebook USB-C', 'Laboratorio 3'),
    ('Casaco preto com capuz', 'Cantina');
