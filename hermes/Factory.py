from hermes.Grammar import Grammar
from hermes.Morpheme import NonTerminal
from hermes.Morpheme import Terminal
from hermes.Morpheme import EmptyString
from hermes.Morpheme import EndOfStream
from hermes.Morpheme import Expression
from hermes.Grammar import Rule, MacroGeneratedRule
from hermes.Grammar import Production
from hermes.Macro import ExprListMacro, SeparatedListMacro, NonterminalListMacro

class Factory:

  def __init__(self):
    self.dirty = False
    self.ε = EmptyString(-1)
    self.λ = Expression(-1)
    self.σ = EndOfStream(-1)
    self.rules = []
    self.terminals = {}
    self.nonterminals = {}
    self.macros = {}
    self.exprRules = []
    self.exprPrecedence = {}
    self.Nc = self.tc = self.Rc = self.Ec = 0
    self.terminals['ε'] = self.ε
    self.terminals['σ'] = self.σ
    self.precedence = 1000

  def reset(self):
    self.__init__()

  def buildGrammar(self, S):
    G = Grammar()
    self.skewIds()
    self.ε.id = self.tc
    self.σ.id = self.tc + 1
    self.λ.id = self.tc + 2
    G.ε = self.ε
    G.σ = self.σ
    G.λ = self.λ
    G.setGrammar( self.nonterminals, self.terminals, self.macros.values(), self.rules, S, self.exprRules, self.exprPrecedence )
    return G

  def addTerminal(self, s, root=False):
    key = s.lower()
    try:
      t = self.terminals[key]
    except KeyError:
      t = Terminal(s, self.tc, root)
      self.terminals[key] = t
      self.tc += 1
    return t

  def addExprTerminal(self):
    try:
      t = self.terminals['λ']
    except KeyError:
      self.terminals['λ'] = self.λ
    return self.terminals['λ']

  def addNonTerminal(self, s, root=False):
    key = s.lower()
    try:
      t = self.nonterminals[key]
    except KeyError:
      t = NonTerminal(s, self.Nc, root)
      self.nonterminals[key] = t
      self.Nc += 1
    return t

  def skewIds(self):
    b = self.tc
    for s,nt in self.nonterminals.items():
      nt.id = b
      b += 1

  def addEmptyString(self):
    return self.addTerminal('ε')

  def addEndString(self):
    return self.addTerminal('σ')

  def addRule(self, rhs, lhs, rhsRootIndex=0, ast=None ):
    r = Rule( rhs, lhs, self.Rc, rhsRootIndex, ast )
    self.rules.append(r)
    self.Rc += 1
    return r
  
  def addMacroGeneratedRule(self, rhs, lhs, rhsRootIndex=0, ast=None):
    r = MacroGeneratedRule( rhs, lhs, self.Rc, rhsRootIndex, ast )
    self.rules.append(r)
    self.Rc += 1
    return r

  def addOperatorPrecedence(self, terminal, bindingPower):
    l = [self.precedence, bindingPower]
    try:
      op = self.exprPrecedence[terminal]
      if terminal not in op:
        self.exprPrecedence[terminal].append(l)
    except KeyError:
      self.exprPrecedence[terminal] = [l]
    self.precedence += 1000

  def addExpressionRule( self, lhs, rhs, rhsRootIndex=0, ast=None ):
    r = Rule( lhs, rhs, self.Ec, rhsRootIndex, ast )
    if rhsRootIndex != 0:
      self.addOperatorPrecedence( rhs.morphemes[rhsRootIndex], 'LEFT' )
    self.exprRules.append(r)
    self.Ec += 1
    self.terminals['λ'] = self.λ
    return r
  
  def addListMacro( self, nonterminal, separator, start, rules, context ):
    if context == 'expr':
      idx = tuple([context, nonterminal, separator])
      obj = ExprListMacro( nonterminal, separator )
    else:
      if separator:
        idx = tuple([context, nonterminal, separator])
        obj = SeparatedListMacro( nonterminal, separator, start, rules)
      else:
        idx = tuple([context, nonterminal])
        obj = NonterminalListMacro( nonterminal, start, rules)
    try:
      m = self.macros[idx]
    except KeyError:
      m = self.macros[idx] = obj
      for r in rules:
        r.nonterminal.macro = obj
    return m