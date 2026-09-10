"""Valida as transcricoes do Anexo 1 contra as tabelas 6.3-6.5 / 6.8-6.10
ja embutidas no CCAE. As classes de A.2 e A.3 sao ORACULO EXTERNO."""
from decimal import Decimal as D

def cls(v, lim):
    v = D(str(v))
    for sup, c in lim:
        if sup is None or v <= D(str(sup)):
            return c
    raise ValueError

# --- classes auxiliares
ARG = [(20.0,"4"),(40.0,"3"),(60.0,"2"),(None,"1")]
CTC = [(7.5,"BAIXA"),(15.0,"MEDIA"),(30.0,"ALTA"),(None,"MUITO_ALTA")]

# --- P: Tab 6.3 / 6.4 / 6.5 (CCAE secao 6, F2)
P = {
 1:{"1":[(5.0,"MB"),(10.0,"B"),(15.0,"M"),(30.0,"A"),(None,"MA")],
    "2":[(7.0,"MB"),(14.0,"B"),(21.0,"M"),(42.0,"A"),(None,"MA")],
    "3":[(10.0,"MB"),(20.0,"B"),(30.0,"M"),(60.0,"A"),(None,"MA")],
    "4":[(17.0,"MB"),(34.0,"B"),(51.0,"M"),(102.0,"A"),(None,"MA")]},
 2:{"1":[(3.0,"MB"),(6.0,"B"),(9.0,"M"),(18.0,"A"),(None,"MA")],
    "2":[(4.0,"MB"),(8.0,"B"),(12.0,"M"),(24.0,"A"),(None,"MA")],
    "3":[(6.0,"MB"),(12.0,"B"),(18.0,"M"),(36.0,"A"),(None,"MA")],
    "4":[(10.0,"MB"),(20.0,"B"),(30.0,"M"),(60.0,"A"),(None,"MA")]},
 3:{"1":[(1.5,"MB"),(3.0,"B"),(4.5,"M"),(9.0,"A"),(None,"MA")],
    "2":[(2.0,"MB"),(4.0,"B"),(6.0,"M"),(12.0,"A"),(None,"MA")],
    "3":[(3.0,"MB"),(6.0,"B"),(9.0,"M"),(18.0,"A"),(None,"MA")],
    "4":[(5.0,"MB"),(10.0,"B"),(15.0,"M"),(30.0,"A"),(None,"MA")]}}

# --- K: Tab 6.8 / 6.9 / 6.10
K = {
 1:{"BAIXA":[(30,"MB"),(60,"B"),(90,"M"),(180,"A"),(None,"MA")],
    "MEDIA":[(45,"MB"),(90,"B"),(135,"M"),(270,"A"),(None,"MA")],
    "ALTA":[(60,"MB"),(120,"B"),(180,"M"),(360,"A"),(None,"MA")],
    "MUITO_ALTA":[(70,"MB"),(140,"B"),(210,"M"),(420,"A"),(None,"MA")]},
 2:{"BAIXA":[(20,"MB"),(40,"B"),(60,"M"),(120,"A"),(None,"MA")],
    "MEDIA":[(30,"MB"),(60,"B"),(90,"M"),(180,"A"),(None,"MA")],
    "ALTA":[(40,"MB"),(80,"B"),(120,"M"),(240,"A"),(None,"MA")],
    "MUITO_ALTA":[(45,"MB"),(90,"B"),(135,"M"),(270,"A"),(None,"MA")]},
 3:{"BAIXA":[(15,"MB"),(30,"B"),(45,"M"),(90,"A"),(None,"MA")],
    "MEDIA":[(20,"MB"),(40,"B"),(60,"M"),(120,"A"),(None,"MA")],
    "ALTA":[(30,"MB"),(60,"B"),(90,"M"),(180,"A"),(None,"MA")],
    "MUITO_ALTA":[(35,"MB"),(70,"B"),(105,"M"),(210,"A"),(None,"MA")]}}

# --- Tabela A.1 transcrita
GLEBAS = {
 1: dict(argila=65, ph=5.4, smp=5.9, p=2.0, k=65, mo=4.0, ca=5.7, mg=3.4,
         al=0.2, ctc=14.2, ctc_ef_pub=9.5, v_pub=65, m_pub=2),
 2: dict(argila=45, ph=5.1, smp=5.8, p=6.2, k=50, mo=2.9, ca=2.1, mg=1.4,
         al=1.0, ctc=8.5, ctc_ef_pub=4.6, v_pub=43, m_pub=22),
 3: dict(argila=12, ph=5.8, smp=5.9, p=12.5, k=25, mo=1.9, ca=2.0, mg=1.1,
         al=0.0, ctc=4.7, ctc_ef_pub=3.2, v_pub=67, m_pub=0),
 4: dict(argila=27, ph=5.3, smp=5.4, p=13.1, k=44, mo=2.1, ca=2.5, mg=1.3,
         al=1.1, ctc=12.7, ctc_ef_pub=5.1, v_pub=31, m_pub=22)}

CULTURAS = {"alho":(1,1), "milho":(2,2), "trigo":(2,2), "eucalipto":(3,3)}

# --- Tab A.2 e A.3 publicadas (oraculo externo)
A2 = {"alho":["MB","MB","MB","B"], "milho":["MB","B","B","M"],
      "trigo":["MB","B","B","M"], "eucalipto":["B","A","M","A"]}
A3 = {"alho":["B","B","MB","MB"], "milho":["M","B","B","B"],
      "trigo":["M","B","B","B"], "eucalipto":["A","M","B","M"]}

print("=" * 66)
print("1) COERENCIA INTERNA DA TABELA A.1")
print("=" * 66)
for g, d in GLEBAS.items():
    kc = d["k"] / 391.0
    s = d["ca"] + d["mg"] + kc
    ctc_ef = s + d["al"]
    v = 100 * s / d["ctc"]
    m = 100 * d["al"] / ctc_ef if ctc_ef else 0.0
    ok = lambda a, b, t=0.6: "OK " if abs(a - b) <= t else "!! "
    print(f"Gleba {g}: V% calc {v:5.1f} vs pub {d['v_pub']:>3} {ok(v,d['v_pub'])}"
          f"| m% calc {m:5.1f} vs pub {d['m_pub']:>3} {ok(m,d['m_pub'])}"
          f"| CTCef calc {ctc_ef:5.2f} vs pub {d['ctc_ef_pub']} "
          f"{ok(ctc_ef,d['ctc_ef_pub'],0.05)}")

print()
print("=" * 66)
print("2) P e K: CCAE vs CLASSES PUBLICADAS (Tab. A.2 / A.3)")
print("=" * 66)
erros = 0
for cult, (gp, gk) in CULTURAS.items():
    lp, lk = [], []
    for g in (1, 2, 3, 4):
        d = GLEBAS[g]
        cp = cls(d["p"], P[gp][cls(d["argila"], ARG)])
        ck = cls(d["k"], K[gk][cls(d["ctc"], CTC)])
        lp.append(cp); lk.append(ck)
        if cp != A2[cult][g-1]: erros += 1; print(f"  DIVERG P {cult} G{g}")
        if ck != A3[cult][g-1]: erros += 1; print(f"  DIVERG K {cult} G{g}")
    print(f"{cult:>10} P(gr.{gp}) calc {lp} | pub {A2[cult]}")
    print(f"{'':>10} K(gr.{gk}) calc {lk} | pub {A3[cult]}")
print(f"\nDivergencias: {erros} de 32 classificacoes")

print()
print("=" * 66)
print("3) CALAGEM: pH e SMP vs texto do Anexo 1 (p. 354)")
print("=" * 66)
SMP60 = {5.4:6.8, 5.5:6.1, 5.6:5.4, 5.7:4.8, 5.8:4.2, 5.9:3.7, 6.0:3.2}
esperado = {1:3.7, 2:4.2, 4:6.8}
for g, d in GLEBAS.items():
    precisa = d["ph"] < 5.5
    dose = SMP60.get(d["smp"])
    tag = ""
    if g in esperado:
        tag = "OK " if abs(dose - esperado[g]) < 0.01 else "!! "
    print(f"Gleba {g}: pH {d['ph']} -> calagem={'SIM' if precisa else 'NAO'}"
          f" | SMP {d['smp']} -> {dose} t/ha {tag}"
          f"{'(esperado ' + str(esperado[g]) + ')' if g in esperado else ''}")

print()
print("=" * 66)
print("4) A-10: a Gleba discrimina 1,5 vs 1,6 na Tab. 6.5 col.1?")
print("=" * 66)
# unico caso em argila classe 1 + grupo 3 = Gleba 1 / eucalipto, P = 2,0
print(f"P=2,0 com limite 1,5 -> {cls(2.0, P[3]['1'])}")
alt = [(1.4,'MB'),(3.0,'B'),(4.5,'M'),(9.0,'A'),(None,'MA')]
print(f"P=2,0 com limite 1,4 -> {cls(2.0, alt)}")
print("Mesmo resultado -> o Anexo 1 NAO resolve a pendencia A-10.")

print()
print("=" * 66)
print("5) COBERTURA: culturas da Tab. 5.1 ausentes do Anexo 2")
print("=" * 66)
anexo2 = {"abobora","alcachofra","alface","alho","aspargo","beringela",
 "beterraba","brocolis","cenoura","cebola","chicoria","chuchu","couve-flor",
 "ervilha","mandioquinha salsa","melancia","melao","moranga","nabo",
 "palmeira real australiana","pepino","pimentao","pupunheira","rabanete",
 "repolho","rucula","salsa","tomateiro","batata-doce","batata","mandioca",
 "amendoim","arroz","arroz irrigado","aveia branca","aveia preta","canola",
 "centeio","cevada","ervilha seca e forrageira","ervilhaca","feijao",
 "girassol","linho","milho","milho pipoca","nabo forrageiro","painco","soja",
 "sorgo","tremoco","trigo","triticale","abacateiro","ameixeira",
 "amoreira-preta","bananeira","caquizeiro","citros","figueira","macieira",
 "maracujazeiro","mirtileiro","morangueiro","nectarineira","nogueira peca",
 "oliveira","palmeira jucara","pereira","pessegueiro","quivizeiro","videira",
 "acacia-negra","araucaria","bracatinga","cedro australiano","erva-mate",
 "eucalipto","pinus","alfavaca","calendula","camomila","capim-limao",
 "citronela-de-java","cardamomo","carqueja","cha","coentro","curcuma",
 "erva-doce","stevia","funcho","hortelas","gengibre","guaco","palma-rosa",
 "piretro","urucum","vetiver","crisantemo de corte","roseira de corte",
 "cana-de-acucar","tabaco","alfafa","pastagem natural"}
tab51_extra = {
 "abobrinha": "aparece na Tab. 5.1 (pH 6,0); NAO consta do Anexo 2",
 "arroz de sequeiro": "Tab. 5.1; provavel = 'Arroz' (2/2) do Anexo 2",
 "almeirao": "Tab. 5.1; = Chicoria (2/2)",
 "manjericao": "Tab. 5.1; = Alfavaca (3/3)",
 "mirtilo": "Tab. 5.1; = Mirtileiro (2/2)",
 "tomate": "Tab. 5.1; = Tomateiro (2/1)",
 "palmeira-real": "Tab. 5.1; = Palmeira real australiana (2/2)",
 "palmeira-jucara": "Tab. 5.1; = Palmeira Jucara (2/2)",
 "consorciacao de gramineas e leguminosas": "Tab. 5.1; sem entrada propria",
 "gramineas/leguminosas forrageiras de estacao fria/quente":
     "Tab. 5.1; Anexo 2 lista especies individuais",
}
for k_, v_ in tab51_extra.items():
    print(f"  - {k_}: {v_}")
