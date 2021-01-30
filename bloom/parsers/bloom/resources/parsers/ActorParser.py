# Generated from bloom/resources/parsers/Actor.g4 by ANTLR 4.9.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\13")
        buf.write("\60\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\3")
        buf.write("\2\7\2\20\n\2\f\2\16\2\23\13\2\3\2\3\2\3\3\3\3\3\3\3\3")
        buf.write("\7\3\33\n\3\f\3\16\3\36\13\3\3\3\3\3\3\4\3\4\3\5\3\5\3")
        buf.write("\5\3\6\3\6\3\7\3\7\7\7+\n\7\f\7\16\7.\13\7\3\7\2\2\b\2")
        buf.write("\4\6\b\n\f\2\3\4\2\6\b\n\n\2,\2\21\3\2\2\2\4\26\3\2\2")
        buf.write("\2\6!\3\2\2\2\b#\3\2\2\2\n&\3\2\2\2\f(\3\2\2\2\16\20\5")
        buf.write("\4\3\2\17\16\3\2\2\2\20\23\3\2\2\2\21\17\3\2\2\2\21\22")
        buf.write("\3\2\2\2\22\24\3\2\2\2\23\21\3\2\2\2\24\25\7\2\2\3\25")
        buf.write("\3\3\2\2\2\26\27\7\3\2\2\27\30\7\6\2\2\30\34\7\4\2\2\31")
        buf.write("\33\5\6\4\2\32\31\3\2\2\2\33\36\3\2\2\2\34\32\3\2\2\2")
        buf.write("\34\35\3\2\2\2\35\37\3\2\2\2\36\34\3\2\2\2\37 \7\5\2\2")
        buf.write(" \5\3\2\2\2!\"\5\b\5\2\"\7\3\2\2\2#$\5\f\7\2$%\5\n\6\2")
        buf.write("%\t\3\2\2\2&\'\t\2\2\2\'\13\3\2\2\2(,\7\n\2\2)+\7\t\2")
        buf.write("\2*)\3\2\2\2+.\3\2\2\2,*\3\2\2\2,-\3\2\2\2-\r\3\2\2\2")
        buf.write(".,\3\2\2\2\5\21\34,")
        return buf.getvalue()


class ActorParser ( Parser ):

    grammarFileName = "Actor.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'Actor'", "'{'", "'}'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "INT", "FLOAT", "STRING", "SUB_PROPERTY_NAME", "ID", 
                      "WHITE_SPACE" ]

    RULE_program = 0
    RULE_actor = 1
    RULE_statement = 2
    RULE_property_definition = 3
    RULE_property_value = 4
    RULE_property_name = 5

    ruleNames =  [ "program", "actor", "statement", "property_definition", 
                   "property_value", "property_name" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    INT=4
    FLOAT=5
    STRING=6
    SUB_PROPERTY_NAME=7
    ID=8
    WHITE_SPACE=9

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class ProgramContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EOF(self):
            return self.getToken(ActorParser.EOF, 0)

        def actor(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ActorParser.ActorContext)
            else:
                return self.getTypedRuleContext(ActorParser.ActorContext,i)


        def getRuleIndex(self):
            return ActorParser.RULE_program

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProgram" ):
                listener.enterProgram(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProgram" ):
                listener.exitProgram(self)




    def program(self):

        localctx = ActorParser.ProgramContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_program)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 15
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==ActorParser.T__0:
                self.state = 12
                self.actor()
                self.state = 17
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 18
            self.match(ActorParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ActorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INT(self):
            return self.getToken(ActorParser.INT, 0)

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ActorParser.StatementContext)
            else:
                return self.getTypedRuleContext(ActorParser.StatementContext,i)


        def getRuleIndex(self):
            return ActorParser.RULE_actor

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterActor" ):
                listener.enterActor(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitActor" ):
                listener.exitActor(self)




    def actor(self):

        localctx = ActorParser.ActorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_actor)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 20
            self.match(ActorParser.T__0)
            self.state = 21
            self.match(ActorParser.INT)
            self.state = 22
            self.match(ActorParser.T__1)
            self.state = 26
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==ActorParser.ID:
                self.state = 23
                self.statement()
                self.state = 28
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 29
            self.match(ActorParser.T__2)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StatementContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def property_definition(self):
            return self.getTypedRuleContext(ActorParser.Property_definitionContext,0)


        def getRuleIndex(self):
            return ActorParser.RULE_statement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStatement" ):
                listener.enterStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStatement" ):
                listener.exitStatement(self)




    def statement(self):

        localctx = ActorParser.StatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_statement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 31
            self.property_definition()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Property_definitionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def property_name(self):
            return self.getTypedRuleContext(ActorParser.Property_nameContext,0)


        def property_value(self):
            return self.getTypedRuleContext(ActorParser.Property_valueContext,0)


        def getRuleIndex(self):
            return ActorParser.RULE_property_definition

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProperty_definition" ):
                listener.enterProperty_definition(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProperty_definition" ):
                listener.exitProperty_definition(self)




    def property_definition(self):

        localctx = ActorParser.Property_definitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_property_definition)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 33
            self.property_name()
            self.state = 34
            self.property_value()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Property_valueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INT(self):
            return self.getToken(ActorParser.INT, 0)

        def FLOAT(self):
            return self.getToken(ActorParser.FLOAT, 0)

        def STRING(self):
            return self.getToken(ActorParser.STRING, 0)

        def ID(self):
            return self.getToken(ActorParser.ID, 0)

        def getRuleIndex(self):
            return ActorParser.RULE_property_value

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProperty_value" ):
                listener.enterProperty_value(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProperty_value" ):
                listener.exitProperty_value(self)




    def property_value(self):

        localctx = ActorParser.Property_valueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_property_value)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 36
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << ActorParser.INT) | (1 << ActorParser.FLOAT) | (1 << ActorParser.STRING) | (1 << ActorParser.ID))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Property_nameContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(ActorParser.ID, 0)

        def SUB_PROPERTY_NAME(self, i:int=None):
            if i is None:
                return self.getTokens(ActorParser.SUB_PROPERTY_NAME)
            else:
                return self.getToken(ActorParser.SUB_PROPERTY_NAME, i)

        def getRuleIndex(self):
            return ActorParser.RULE_property_name

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterProperty_name" ):
                listener.enterProperty_name(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitProperty_name" ):
                listener.exitProperty_name(self)




    def property_name(self):

        localctx = ActorParser.Property_nameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_property_name)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 38
            self.match(ActorParser.ID)
            self.state = 42
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==ActorParser.SUB_PROPERTY_NAME:
                self.state = 39
                self.match(ActorParser.SUB_PROPERTY_NAME)
                self.state = 44
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





