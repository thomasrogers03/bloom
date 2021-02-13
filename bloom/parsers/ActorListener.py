# Generated from Actor.g4 by ANTLR 4.9.1
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .ActorParser import ActorParser
else:
    from ActorParser import ActorParser

# This class defines a complete listener for a parse tree produced by ActorParser.
class ActorListener(ParseTreeListener):

    # Enter a parse tree produced by ActorParser#program.
    def enterProgram(self, ctx: ActorParser.ProgramContext):
        pass

    # Exit a parse tree produced by ActorParser#program.
    def exitProgram(self, ctx: ActorParser.ProgramContext):
        pass

    # Enter a parse tree produced by ActorParser#actor.
    def enterActor(self, ctx: ActorParser.ActorContext):
        pass

    # Exit a parse tree produced by ActorParser#actor.
    def exitActor(self, ctx: ActorParser.ActorContext):
        pass

    # Enter a parse tree produced by ActorParser#statement.
    def enterStatement(self, ctx: ActorParser.StatementContext):
        pass

    # Exit a parse tree produced by ActorParser#statement.
    def exitStatement(self, ctx: ActorParser.StatementContext):
        pass

    # Enter a parse tree produced by ActorParser#property_definition.
    def enterProperty_definition(self, ctx: ActorParser.Property_definitionContext):
        pass

    # Exit a parse tree produced by ActorParser#property_definition.
    def exitProperty_definition(self, ctx: ActorParser.Property_definitionContext):
        pass

    # Enter a parse tree produced by ActorParser#property_value.
    def enterProperty_value(self, ctx: ActorParser.Property_valueContext):
        pass

    # Exit a parse tree produced by ActorParser#property_value.
    def exitProperty_value(self, ctx: ActorParser.Property_valueContext):
        pass

    # Enter a parse tree produced by ActorParser#property_name.
    def enterProperty_name(self, ctx: ActorParser.Property_nameContext):
        pass

    # Exit a parse tree produced by ActorParser#property_name.
    def exitProperty_name(self, ctx: ActorParser.Property_nameContext):
        pass


del ActorParser
