#!/usr/bin/env python

import subprocess
from optparse import OptionParser
import sys, os, random
import time;
import numpy as np
from scipy import stats
from collections import Counter,defaultdict
from operator import itemgetter 
from random import randint
import operator
from Bio import SeqIO
from Bio.Seq import Seq


def reversecomplement(sequence):
    complement = {"A":"T", "T":"A", "C":"G", "G":"C", "N":"N"}
    reverse_complement_sequence = ""
    sequence_list = list(sequence)
    sequence_list.reverse()
    for letter in sequence_list:
        reverse_complement_sequence += complement[letter.upper()];
    return reverse_complement_sequence;


def which(program):
    sys.stderr.write("Detecting program: "+str(program)+"\n");
    cjob = "type "+str(program);

    sp = subprocess.Popen(["/bin/bash", "-i", "-c", cjob],
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
    

    out, err = sp.communicate();
    errcode  = sp.returncode;
    if(errcode != 0): #has finished but wrong code
        sys.stderr.write("Cannot find program: "+str(program)+" please make sure it is installed\n");
        sys.exit(1);
    

    if(out.find("aliased") != -1): #was aliased
        return out[out.find(" to ")+5:-2];
    else:
        if(out.find(" is ") != -1):
            return out[out.find(" is ")+4:];
        else:
            sys.stderr.write("Cannot seem to find program: "+str(program)+" please make sure it is installed\n");
            sys.exit(1);
            

	

    return out;



def handle_job(cjob):

    print str(cjob);
    jobcreated=subprocess.Popen(cjob,shell=True,
                                executable="/bin/bash",
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE); 
    jobcreated.wait()

    out, err = jobcreated.communicate()
    errcode  = jobcreated.returncode;
	
    if(errcode != 0): #has finished but wrong code
        print "Job failed "+cjob+" failed";
        sys.exit(1);

    return out;


parser = OptionParser("$prog [options]")
parser.add_option("-t", "--theta",      dest="theta",        help="Theta",                          default=20,      type="float");
parser.add_option("-s", "--timesplit",  dest="timesplit",    help="Split time in 2N_0 generations", default=0.10,    type="float");
parser.add_option("-f", "--destfolder", dest="destfolder",   help="Output folder",                  default=None,    type="string");
parser.add_option("-n", "--numsim",     dest="numsim",       help="Number of simulations",          default=100,     type="int");
parser.add_option(""  , "--branchl",    dest="branchlscale", help="Seqgen branch scale",            default=0.00045, type="float");
parser.add_option(""  , "--chrlen",     dest="lengthchr",    help="Chromosome length",              default=10000,   type="int");
parser.add_option("-u", "--numtotalhum", dest="numtotalhum",help="Number of human contaminants, default and minimum is 2 (1 for cont. 1 for reference)", default=3, type="int")





#print handle_job("which ls");

(options,args) = parser.parse_args()

#detecting programs
mscmd     = which("ms");
seqgencmd = which("seq-gen");

theta        = options.theta
timesplit    = options.timesplit
destfolder   = options.destfolder
numsim       = options.numsim

if(destfolder ==  None):
    print "Please specify the output folder";
    sys.exit(1);




sizeendogenous     = [];
sizecontaminant    = [];
sumsizeendogenous  = 0;
sumsizecontaminant = 0;


timesplitms = timesplit / 2.0

#numsamphum  = 6
numtotalhum = options.numtotalhum;
if(numtotalhum < 2 ):
    print "Please specify at least 2 contaminant humans";
    sys.exit(1);

#numtotalhum = 3 #2 humans for sample + 1 for reference
numarch     = 2
#seq-gen

lengthchr    = options.lengthchr;
branchlscale = options.branchlscale;

puredict    = defaultdict(int)
i=1
#try:
if not os.path.exists(destfolder):
    os.mkdir(destfolder);

if not os.path.exists(destfolder+"/cont/"):
    os.mkdir(destfolder+"/cont/");

if not os.path.exists(destfolder+"/bact/"):
    os.mkdir(destfolder+"/bact/");

if not os.path.exists(destfolder+"/endo/"):
    os.mkdir(destfolder+"/endo/");

if not os.path.exists(destfolder+"/endo/"):
    os.mkdir(destfolder+"/endo/");

if os.path.exists(""+destfolder+"/ref.fa"):
    os.remove(""+destfolder+"/ref.fa");

if os.path.exists(""+destfolder+"endo/endo.1.fa"):
    os.remove(""+destfolder+"endo/endo.1.fa");

if os.path.exists(""+destfolder+"endo/endo.2.fa"):
    os.remove(""+destfolder+"endo/endo.2.fa");


for idseq in range((numtotalhum+1),(numtotalhum+1+numarch)):
    if os.path.exists(""+destfolder+"cont/cont."+str(idseq-(numtotalhum+1))+".fa" ):
        os.remove( ""+destfolder+"cont/cont."+str(idseq-(numtotalhum+1))+".fa" );



i=1;
originali=0;

while i < (numsim+1):
    
	# Create simulation file
	originali += 1;    
	infile_name = ""+destfolder+"/simul_"+str(i)+".txt"

        commname = ""+mscmd+" "+str(numtotalhum+numarch)+" 1 -T -t "+str(theta)+" -I 2 "+str(numtotalhum)+" "+str(numarch)+" -ej "+str(timesplitms)+" 1 2 "
        print commname

	commname = commname + " > "+infile_name+"_tmp";
	handle_job(commname);

        commname3 = "cat "+infile_name+"_tmp | grep '('   > "+infile_name+"_tree";
	handle_job(commname3);

        commname4 = ""+seqgencmd+"    -mHKY -l "+str(lengthchr)+" -s "+str(branchlscale)+"   "+infile_name+"_tree |tail -n+2  |awk '{print \">\"$1\"\\n\"$2}'  > "+infile_name+".fa";
	handle_job(commname4);

	#try:
	if True:	
		print "simul number "+str(originali)

		myid2seq = {};

		handle = open(infile_name+".fa", "rU")

		for record in SeqIO.parse(handle, "fasta") :
			#print str(record.id);
			myid2seq[ record.id  ] = str(record.seq);
		handle.close();
                
                commname4 = "gzip -f "+infile_name+".fa";
                handle_job(commname4);

                

		arrayHumans  = [];
		arrayNeander = [];
		ancSeq = "";

		#print record.id+"\t"+str(len(record.seq));
                #seq1:first chr endo
                #seq2:second chr endo
                #seq3:reference
                #seq4:first chr cont
                #seq5:second chr cont


                #will be endogenous
		for idseq in range(1,numtotalhum):
                    print "endo seq#"+str(idseq);
                    arrayNeander.append( myid2seq[ str(idseq)  ] ); #ancSeq= myid2seq[ str(numtotalhum+1+numarch)  ];#anc
                print "ref. seq#3";

                #will be contaminant
		for idseq in range((numtotalhum+1),(numtotalhum+1+numarch)):
                    print "cont seq#"+str(idseq);
                    arrayHumans.append( myid2seq[ str(idseq)  ] ); 			#print str(idseq);

		#print str(len(arrayHumans));
		#print str(len(arrayNeander));



		#take #3 as the reference
		fileHandleWriteREF = open (""+destfolder+"/ref.fa", 'a' ) ;
		fileHandleWriteREF.write(">ref_"+str(originali)+ "\n"+myid2seq[ str(3)  ]+"\n");
		fileHandleWriteREF.close();
                
                fileHandleEndoSeq1 = open (""+destfolder+"endo/endo.1.fa", 'a' );
                fileHandleEndoSeq1.write(">endo_"+str(originali)+ "\n"+myid2seq[ str(1)  ]+"\n");
                fileHandleEndoSeq1.close();

                fileHandleEndoSeq2 = open (""+destfolder+"endo/endo.2.fa", 'a' );
                fileHandleEndoSeq2.write(">endo_"+str(originali)+ "\n"+myid2seq[ str(2)  ]+"\n");
                fileHandleEndoSeq2.close();


                segsites=0;
                #segsiteslist=[];
		#destfolder+"/all.sam.gz";

                if(originali == 1):
                    fileHandleSS = open ( ""+destfolder+"/endo/segsites", 'w' ) ;
                else:
                    fileHandleSS = open ( ""+destfolder+"/endo/segsites", 'a' ) ;

                for seqindex in range(0,lengthchr):
                    if( myid2seq[ str(1) ][seqindex] != myid2seq[ str(2) ][seqindex]):
                        segsites+=1;
                        fileHandleSS.write(">ref_"+str(originali)+ "\t"+str(seqindex+1)+"\t"+myid2seq[ str(1) ][seqindex]+"\t"+myid2seq[ str(2) ][seqindex]+"\n");

                print "het. rate: "+str(float(segsites)/float(lengthchr));                
		fileHandleSS.close();
                print "Wrote segregating sites to "+str(destfolder)+"/endo/segsites";


                for idseq in range((numtotalhum+1),(numtotalhum+1+numarch)):
                    fileHandleContSeq = open (""+destfolder+"cont/cont."+str(idseq-(numtotalhum+1))+".fa", 'a' ) ;
                    fileHandleContSeq.write(">cont_"+str(originali)+ "\n"+myid2seq[ str(idseq)  ]+"\n");
                fileHandleContSeq.close();

	#os.remove(infile_name)
        i += 1;





sys.stderr.write("\nProgram finished succesfully\n");
sys.exit(0);



