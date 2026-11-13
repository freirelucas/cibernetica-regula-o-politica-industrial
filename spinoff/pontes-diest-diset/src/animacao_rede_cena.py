"""Cena manim: a rede DIEST×DISET se reconfigura quando um rótulo muda (simulação).

Consome data/animacao_rede.json (gerado por src/animacao_rede_prep.py) e não grava nada
em data/. Renderizar:
    manim -qm src/animacao_rede_cena.py ReconfiguracaoRede
"""
import json
import math
import os

from manim import (BLACK, DOWN, LEFT, RIGHT, UP, WHITE, Circle, Dot, FadeIn, FadeOut,
                   Line, Scene, Text, ValueTracker, VGroup, Write, always_redraw, config,
                   interpolate_color, ManimColor)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "animacao_rede.json")

COR = {"DIEST": ManimColor("#4C8DD6"), "DISET": ManimColor("#E08A3C")}
MISTA = ManimColor("#F2D15A")
CINZA = ManimColor("#5A6270")
ESCALA_X, ESCALA_Y = 2.1, 1.25
config.background_color = ManimColor("#14171E")


def interp(p0, p1, t):
    return [(1 - t) * p0[0] + t * p1[0], (1 - t) * p0[1] + t * p1[1]]


def tela(p):
    return (p[0] * ESCALA_X, p[1] * ESCALA_Y - 0.45, 0)  # desce a rede para longe do título


class ReconfiguracaoRede(Scene):
    def construct(self):
        d = json.load(open(DATA, encoding="utf-8"))
        alvo_id = d["alvo"]["id"]
        nos = {n["id"]: n for n in d["nos"]}
        arestas = d["arestas"]
        m0 = d["contagem_obras_mistas"]["antes"]
        m1 = d["contagem_obras_mistas"]["depois"]

        t = ValueTracker(0.0)  # 0 = rede atual, 1 = rede com o rótulo alterado

        titulo = Text("Pontes DIEST × DISET: reconfiguração da rede", font_size=22, color=WHITE)
        titulo.to_corner(UP + LEFT, buff=0.4)
        aviso = Text(
            f"Simulação: {d['alvo']['nome']} reclassificada de {d['alvo']['de']} para "
            f"{d['alvo']['para']}. Nada é gravado; os resultados publicados não mudam.",
            font_size=16, color=ManimColor("#AEB4BF"),
        ).to_edge(DOWN, buff=0.25)

        def pos(n):
            return interp(n["pos0"], n["pos1"], t.get_value())

        def grupo(n):
            return n["grupo0"] if t.get_value() < 0.5 else n["grupo1"]

        dots = {}
        for n in nos.values():
            r = 0.05 + 0.025 * math.sqrt(n["obras"])
            dot = always_redraw(lambda n=n, r=r: Dot(
                tela(pos(n)), radius=min(r, 0.16),
                color=COR[grupo(n)] if n["id"] != alvo_id else COR[grupo(n)],
                fill_opacity=0.9, stroke_width=0.6, stroke_color=BLACK))
            dots[n["id"]] = dot

        linhas = []
        for e in arestas:
            a, b = e["a"], e["b"]
            w = 0.6 + 0.35 * min(e["w"], 4)

            def faz(e=e, a=a, b=b, w=w):
                mista = e["mista0"] if t.get_value() < 0.5 else e["mista1"]
                cor = MISTA if mista else CINZA
                op = 0.85 if mista else 0.22
                return Line(tela(pos(nos[a])), tela(pos(nos[b])),
                            stroke_width=w if mista else 0.8,
                            color=cor, stroke_opacity=op)
            linhas.append(always_redraw(faz))

        rotulos = VGroup()
        for n in nos.values():
            if n["rotulo"]:
                rotulos.add(always_redraw(lambda n=n: Text(
                    n["nome"], font_size=12, color=WHITE).move_to(
                        tela(pos(n)) + UP * 0.22)))

        contador = always_redraw(lambda: Text(
            f"obras mistas: {round(m0 + (m1 - m0) * t.get_value())}",
            font_size=22, color=MISTA).to_corner(UP + RIGHT, buff=0.4))

        legenda = VGroup(*[VGroup(ico, Text(txt, font_size=14)).arrange(RIGHT, buff=0.2)
                           for ico, txt in [
            (Dot(color=COR["DIEST"], radius=0.08), "DIEST"),
            (Dot(color=COR["DISET"], radius=0.08), "DISET"),
            (Line(LEFT * 0.2, RIGHT * 0.2, color=MISTA, stroke_width=3), "obra mista"),
            (Line(LEFT * 0.2, RIGHT * 0.2, color=CINZA), "só um lado")]]).arrange(DOWN, buff=0.22, aligned_edge=LEFT).to_corner(DOWN + LEFT, buff=0.6)

        self.add(titulo, aviso)
        self.play(FadeIn(VGroup(*dots.values())), FadeIn(VGroup(*linhas)),
                  Write(legenda), run_time=2)
        self.add(*dots.values(), *linhas, rotulos, contador)
        self.wait(1)

        alvo_dot = dots[alvo_id]
        anel = always_redraw(lambda: Circle(radius=0.3, color=WHITE, stroke_width=2).move_to(
            tela(pos(nos[alvo_id]))))
        self.play(FadeIn(anel), run_time=0.8)
        self.wait(0.8)

        self.play(t.animate.set_value(1.0), run_time=6, rate_func=lambda x: x * x * (3 - 2 * x))
        self.wait(0.5)
        self.play(FadeOut(anel), run_time=0.5)
        self.wait(2)
