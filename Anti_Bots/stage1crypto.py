while ecx < 113:
	edx = 0x0ce # ?
	eax = esi = ecx = None #iteartor
	eax += magic[esi]
	magic[ecx] ^= edx
	ecx = ecx+1
	eax = 0x0cccccc
	eax = ecx
	edx = edx>>2 # div by 4
	eax = edx
	eax = !eax  #negate
	eax = 3*eax - edx
	esi = esi+1

#this is the code changer!!!
#magic happens here