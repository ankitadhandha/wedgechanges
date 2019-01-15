name = 'Python Server Pages'

version = (0, 8, 1)

docs = [ {'name': "User's Guide", 'file': 'UsersGuide.html'} ]

status = 'beta'

requiredPyVersion = (2, 0, 0)

synopsis = """A Python Server Page (or PSP) is an HTML document with interspersed Python instructions that are interpreted to generate dynamic content. PSP is analogous to PHP, Microsoft's ASP and Sun's JSP. PSP sits on top of (and requires) WebKit and therefore benefits from its features."""



WebKitConfig = {
	'examplePages': [
		'Hello',
		'Braces',
		'PSPTests',
		'PSPTests-Braces',
	]
}
