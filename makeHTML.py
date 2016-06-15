# Taken from "makeHTML" (http://www.hoboes.com/library/downloads/makeHTML.py.gz)
# Copyright by Jerry Stratton
#   (http://www.hoboes.com/Mimsy/hacks/object-oriented-html/)

# Basic classes
class newTag:
    def __init__(self, code, content=None, style=None, id=None, attributes=None, newlines=True):
        self.id = id
        self.pieces = []
        self.code = code
        self.newlines = newlines

        if attributes == None:
            self.attributes = {}
        else:
            self.attributes = attributes

        if isinstance(content, list):
            self.addPieces(content)
        elif content != None:
            self.addPiece(content)

    def __len__(self):
        return len(self.pieces)

    def addID(self, ID):
        if self.id:
            raise IdAlreadyAssignedException('"%r"'%self.id)
        assert(isinstance(ID, basestring))
        self.id = ID

    def popID(self):
        assert(self.id)
        ID = self.id
        self.id = None
        return ID

    def addAttribute(self, attributename, attributevalue):
        self.attributes[attributename] = attributevalue

    def addAttributes(self, attributes):
        for attributename, attributevalue in attributes.iteritems():
            self.addAttribute(attributename, attributevalue)

    def addPart(self, code, content=None, style=None, id=None, attributes=None):
        newPart = self.makePart(code, content, style, id, attributes)
        self.addPiece(newPart)

    def addPiece(self, thePart):
        self.pieces.append(thePart)

    def addPieces(self, theParts):
        if theParts != None:
            if isinstance(theParts, list):
                for part in theParts:
                    self.addPiece(part)
            else:
                self.addPiece(theParts)

    def insertPart(self, code, content=None, style=None, id=None, attributes=None):
        newPart = self.makePart(code, content, style, id, attributes)
        self.insertPiece(newPart)

    def insertPiece(self, thePart):
        self.pieces.insert(0, thePart)

    def make(self, tab="\t", level=0):
        startHTML = '<' + self.code

        if (self.attributes):
            for attribute in self.attributes:
                content = self.attributes[attribute]
                if content == None:
                    startHTML += ' ' + attribute
                else:
                    startHTML += ' ' + attribute + '="' + str(content) + '"'

        if (self.id):
            startHTML += ' id="' + self.id + '"'

        if self.pieces:
            startHTML += '>'

            partItems = [startHTML]

            if len(self.pieces) > 1 and self.newlines:
                finalSep = "\n" + tab*level
                sep = finalSep + tab
            else:
                finalSep = ""
                sep = ""

            for piece in self.pieces:
                if isinstance(piece, basestring):
                    partItems.append(piece)
                elif isinstance(piece, int) or isinstance(piece, float):
                    partItems.append(str(piece))
                elif isinstance(piece, newTag):
                    partItems.append(piece.make(tab, level=level+1))
                elif piece == None:
                    raise Exception('TAG: "%s"'%self.code)
                    partItems.append("")
                else:
                    assert(False)

            code = sep.join(partItems)
            code += finalSep + '</' + self.code + '>'
            return code

        else:
            startHTML += ' />'
            return startHTML

    def makePart(self, code, content=None, style=None, id=None, attributes=None):
        newPart = newTag(code, content, style, id, attributes)

        return newPart

def Comment(comment):
    return '\n<!--\n    ' + comment + '\n' + (' '*(4+len(comment))) + '-->'

class IdAlreadyAssignedException(Exception):
    pass
