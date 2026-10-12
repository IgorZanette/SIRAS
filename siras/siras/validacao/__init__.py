"""
Apuração da validação: executa os casos com oráculo e mede a concordância.

Camada separada do motor de propósito. O motor produz recomendação; isto aqui mede o
quanto ela bate com a referência calculada à mão pelo autor. Misturar os dois faria o
sistema avaliar a si mesmo com o próprio código que está sendo avaliado.

Não importa Flask, como `siras/motor/` e `siras/dominio/`: roda por linha de comando.
"""
