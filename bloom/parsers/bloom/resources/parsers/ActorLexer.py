# Generated from bloom/resources/parsers/Actor.g4 by ANTLR 4.9.1
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\13")
        buf.write("S\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\3\2\3\2\3\2\3\2\3\2\3\2\3\3\3")
        buf.write("\3\3\4\3\4\3\5\5\5!\n\5\3\5\6\5$\n\5\r\5\16\5%\3\6\5\6")
        buf.write(")\n\6\3\6\6\6,\n\6\r\6\16\6-\3\6\3\6\6\6\62\n\6\r\6\16")
        buf.write("\6\63\3\7\3\7\7\78\n\7\f\7\16\7;\13\7\3\7\3\7\3\b\3\b")
        buf.write("\3\b\3\t\6\tC\n\t\r\t\16\tD\3\t\7\tH\n\t\f\t\16\tK\13")
        buf.write("\t\3\n\6\nN\n\n\r\n\16\nO\3\n\3\n\39\2\13\3\3\5\4\7\5")
        buf.write("\t\6\13\7\r\b\17\t\21\n\23\13\3\2\b\3\2//\3\2\62;\3\2")
        buf.write("\60\60\5\2C\\aac|\6\2\62;C\\aac|\5\2\13\f\17\17\"\"\2")
        buf.write("[\2\3\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13")
        buf.write("\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3")
        buf.write("\2\2\2\3\25\3\2\2\2\5\33\3\2\2\2\7\35\3\2\2\2\t \3\2\2")
        buf.write("\2\13(\3\2\2\2\r\65\3\2\2\2\17>\3\2\2\2\21B\3\2\2\2\23")
        buf.write("M\3\2\2\2\25\26\7C\2\2\26\27\7e\2\2\27\30\7v\2\2\30\31")
        buf.write("\7q\2\2\31\32\7t\2\2\32\4\3\2\2\2\33\34\7}\2\2\34\6\3")
        buf.write("\2\2\2\35\36\7\177\2\2\36\b\3\2\2\2\37!\t\2\2\2 \37\3")
        buf.write("\2\2\2 !\3\2\2\2!#\3\2\2\2\"$\t\3\2\2#\"\3\2\2\2$%\3\2")
        buf.write("\2\2%#\3\2\2\2%&\3\2\2\2&\n\3\2\2\2\')\t\2\2\2(\'\3\2")
        buf.write("\2\2()\3\2\2\2)+\3\2\2\2*,\t\3\2\2+*\3\2\2\2,-\3\2\2\2")
        buf.write("-+\3\2\2\2-.\3\2\2\2./\3\2\2\2/\61\7\60\2\2\60\62\t\3")
        buf.write("\2\2\61\60\3\2\2\2\62\63\3\2\2\2\63\61\3\2\2\2\63\64\3")
        buf.write("\2\2\2\64\f\3\2\2\2\659\7$\2\2\668\13\2\2\2\67\66\3\2")
        buf.write("\2\28;\3\2\2\29:\3\2\2\29\67\3\2\2\2:<\3\2\2\2;9\3\2\2")
        buf.write("\2<=\7$\2\2=\16\3\2\2\2>?\t\4\2\2?@\5\21\t\2@\20\3\2\2")
        buf.write("\2AC\t\5\2\2BA\3\2\2\2CD\3\2\2\2DB\3\2\2\2DE\3\2\2\2E")
        buf.write("I\3\2\2\2FH\t\6\2\2GF\3\2\2\2HK\3\2\2\2IG\3\2\2\2IJ\3")
        buf.write("\2\2\2J\22\3\2\2\2KI\3\2\2\2LN\t\7\2\2ML\3\2\2\2NO\3\2")
        buf.write("\2\2OM\3\2\2\2OP\3\2\2\2PQ\3\2\2\2QR\b\n\2\2R\24\3\2\2")
        buf.write("\2\f\2 %(-\639DIO\3\b\2\2")
        return buf.getvalue()


class ActorLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    T__2 = 3
    INT = 4
    FLOAT = 5
    STRING = 6
    SUB_PROPERTY_NAME = 7
    ID = 8
    WHITE_SPACE = 9

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'Actor'", "'{'", "'}'" ]

    symbolicNames = [ "<INVALID>",
            "INT", "FLOAT", "STRING", "SUB_PROPERTY_NAME", "ID", "WHITE_SPACE" ]

    ruleNames = [ "T__0", "T__1", "T__2", "INT", "FLOAT", "STRING", "SUB_PROPERTY_NAME", 
                  "ID", "WHITE_SPACE" ]

    grammarFileName = "Actor.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.1")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


