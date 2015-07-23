"""
.. note::
         These are the plotting functions for the SPLAT code 
"""


# Related third party imports.
import matplotlib.cm as cm
import matplotlib.colors as colmap
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy
from scipy.interpolate import interp1d 
import splat

def plotSpectrum(*args, **kwargs):
    '''
    :Purpose: ``Primary plotting program for Spectrum objects.``

    :Input
    Spectrum objects, either sequentially, in list, or in list of lists
            - Spec1, Spec2, ...: plot multiple spectra together, or separately if multiplot = True
            - [Spec1, Spec2, ...]: plot multiple spectra together, or separately if multiplot = True
            - [[Spec1, Spec2], [Spec3, Spec4], ..]: plot multiple sets of spectra (multiplot forced to be True)

    :Parameters
    file or filename or output:
        filename or filename base for output
    filetype = 'pdf':
        output filetype, generally determined from filename
    multiplot = False: 
        creates multiple plots, depending on format of input (optional)
    multipage = False: 
        spreads plots across multiple pages; output file format must be PDF
        if not set and plots span multiple pages, these pages are output sequentially as separate files
    layout or multilayout = [1,1]:
        defines how multiple plots are laid out on a page
    figsize:
        set the figure size; set to default size if not indicated
    interactive = False:
        if plotting to window, set this to make window interactive
    grid = False:
        add a grid


    title = ''
        string giving plot title
    xlabel:
        wavelength axis label; by default set by wlabel and wunit keywords in first spectrum object
    ylabel:
        flux axis label; by default set by fscale, flabel and funit keywords in first spectrum object
    legend, legends, label or labels:
        list of strings providing legend-style labels for each spectrum plotted
    legendLocation or labelLocation = 'upper right':
        place of legend; options are 'upper left', 'center middle', 'lower right' (variations thereof) and 'outside'
    features:
        a list of strings indicating chemical features to label on the spectra
        options include H2O, CH4, CO, TiO, VO, FeH, H2, HI, KI, NaI, SB (for spectral binary)
    mdwarf, ldwarf, tdwarf, young, binary = False:
        add in features characteristic of these classes
    telluric = False:
        mark telluric absorption features

    stack = 0:
        set to a numerical offset to stack spectra on top of each other
    zeropoint = [0,...]:
        list of offsets for each spectrum, giving finer control than stack
    showZero = True:
        plot the zeropoint(s) of the spectra
    comparison:
        a comparison Spectrum to compare in each plot, useful for common reference standard
    noise, showNoise or uncertainty = False:
        plot the uncertainty for each spectrum

    color or colors:
        color of plot lines; by default all black
    colorUnc or colorsUnc:
        color of uncertainty lines; by default same as line color but reduced opacity
    colorScheme or colorMap:
        color map to apply based on matplotlib colormaps; 
        see http://matplotlib.org/api/pyplot_summary.html?highlight=colormaps#matplotlib.pyplot.colormaps
    linestyle:
        line style of plot lines; by default all solid

    xrange = [0.85,2.42]:
        plot range for wavelength axis
    yrange = [-0.02,1.2]*fluxMax:
        plot range for wavelength axis
        
        
    :Example 1: A simple view of a random spectrum
       >>> import splat
       >>> spc = splat.getSpectrum(spt = 'T5', lucky=True)[0]
       >>> spc.plot()                       # this automatically generates a "quicklook" plot
       >>> splat.plotSpectrum(spc)          # does the same thing
       >>> splat.plotSpectrum(spc,uncertainty=True,tdwarf=True)     # show the spectrum uncertainty and T dwarf absorption features

    :Example 2: Viewing a set of spectra for a given object
        In this case we'll look at all of the spectra of TWA 30B in the library, sorted by year and compared to the first epoch data
        This is an example of using multiplot and multipage

       >>> splist = splat.getSpectrum(name = 'TWA 30B')         # get all spectra of TWA 30B
       >>> junk = [sp.normalize() for sp in splist]             # normalize the spectra
       >>> dates = [sp.date for sp in splist]                   # observation dates
       >>> spsort = [s for (s,d) in sorted(zip(dates,splis))]   # sort spectra by dates
       >>> dates.sort()                                         # don't forget to sort dates!
       >>> splat.plotSpectrum(spsort,multiplot=True,layout=[2,2],multipage=True,\   # here's our plot statement
           comparison=spsort[0],uncertainty=True,mdwarf=True,telluric=True,legends=dates,\
           legendLocation='lower left',output='TWA30B.pdf')
       
    :Example 3: Display the spectra sequence of L dwarfs
        This example uses the list of standard files contained in SPLAT, and illustrates the stack feature

       >>> spt = [splat.typeToNum(i+20) for i in range(10)]     # generate list of L spectral types
       >>> files = [splat.spex_stdfiles[s] for s in spt]        # get the standard files
       >>> splist = [splat.Spectrum(f) for f in files]          # read in list of Spectrum objects
       >>> junk = [sp.normalize() for sp in splist]             # normalize the spectra
       >>> labels = [sp.shortname for sp in splist]              # set labels to be names
       >>> splat.plotSpectrum(splist,figsize=[10,20],labels=labels,stack=0.5,\  # here's our plot statement
           colorScheme='copper',legendLocation='outside',telluric=True,output='lstandards.pdf')
       
    '''

# keyword parameters
    nsamples = kwargs.get('nsamples',1000)
    multiplot = kwargs.get('multiplot',False)           # create multiple plots
    multipage = kwargs.get('multipage',False)           # create a multiple page sequence of plots
    multilayout = kwargs.get('multilayout',[1,1])       # layout of multiple plots, [# horizontal, # vertical]
    multilayout = kwargs.get('layout',multilayout)      
    stack = kwargs.get('stack',0)                   # stack spectra on top of each other
    grid = kwargs.get('grid',False)                 # plot internal grid lines
    filename = kwargs.get('filename','')            # output filename
    filename = kwargs.get('file',filename)
    filename = kwargs.get('output',filename)
    title = kwargs.get('title','')
    filebase = filename.split('.')[0]               # filebase for multiple files
    filetype = kwargs.get('format',filename.split('.')[-1])
    filetype.lower()
    if filetype == '':
        filetype = 'pdf'
    comparison = kwargs.get('comparison',False)
    if comparison.__class__.__name__ != 'Spectrum':
        comparison = False

#    mask = kwargs.get('mask',False)                # not yet implemented

# features to label on spectra
    feature_labels = { \
        'h2o': {'label': r'H$_2$O', 'type': 'band', 'wavelengths': [[0.92,0.95],[1.08,1.20],[1.325,1.550],[1.72,2.14]]}, \
        'ch4': {'label': r'CH$_4$', 'type': 'band', 'wavelengths': [[1.1,1.24],[1.28,1.44],[1.6,1.76],[2.2,2.35]]}, \
        'co': {'label': r'CO', 'type': 'band', 'wavelengths': [[2.28,2.39]]}, \
        'tio': {'label': r'TiO', 'type': 'band', 'wavelengths': [[0.76,0.80],[0.825,0.831]]}, \
        'vo': {'label': r'VO', 'type': 'band', 'wavelengths': [[1.04,1.08]]}, \
        'feh': {'label': r'FeH', 'type': 'band', 'wavelengths': [[0.86,0.90],[0.98,1.03],[1.19,1.25],[1.57,1.64]]}, \
        'h2': {'label': r'H$_2$', 'type': 'band', 'wavelengths': [[2.05,2.6]]}, \
        'sb': {'label': r'*', 'type': 'band', 'wavelengths': [[1.6,1.64]]}, \
        'h': {'label': r'H I', 'type': 'line', 'wavelengths': [[1.004,1.005],[1.093,1.094],[1.281,1.282],[1.944,1.945],[2.166,2.166]]},\
        'hi': {'label': r'H I', 'type': 'line', 'wavelengths': [[1.004,1.005],[1.093,1.094],[1.281,1.282],[1.944,1.945],[2.166,2.166]]},\
        'h1': {'label': r'H I', 'type': 'line', 'wavelengths': [[1.004,1.005],[1.093,1.094],[1.281,1.282],[1.944,1.945],[2.166,2.166]]},\
        'na': {'label': r'Na I', 'type': 'line', 'wavelengths': [[0.8186,0.8195],[1.136,1.137],[2.206,2.209]]}, \
        'nai': {'label': r'Na I', 'type': 'line', 'wavelengths': [[0.8186,0.8195],[1.136,1.137],[2.206,2.209]]}, \
        'na1': {'label': r'Na I', 'type': 'line', 'wavelengths': [[0.8186,0.8195],[1.136,1.137],[2.206,2.209]]}, \
        'k': {'label': r'K I', 'type': 'line', 'wavelengths': [[0.7699,0.7665],[1.169,1.177],[1.244,1.252]]}, \
        'ki': {'label': r'K I', 'type': 'line', 'wavelengths': [[0.7699,0.7665],[1.169,1.177],[1.244,1.252]]}, \
        'k1': {'label': r'K I', 'type': 'line', 'wavelengths': [[0.7699,0.7665],[1.169,1.177],[1.244,1.252]]}}

    features = kwargs.get('features',[])
    if (kwargs.get('ldwarf',False) or kwargs.get('mdwarf',False)):
        features.extend(['k','na','feh','tio','co','h2o','h2'])
    if (kwargs.get('tdwarf',False)):
        features.extend(['k','ch4','h2o','h2'])
    if (kwargs.get('young',False)):
        features.extend(['vo'])
    if (kwargs.get('binary',False)):
        features.extend(['sb'])
# clean repeats while maintaining order - set does not do this
    fea = []
    for i in features:
        if i not in fea:
            fea.append(i)
    features = fea

# error check - make sure you're plotting something
    if (len(args) < 1):
        print 'plotSpectrum needs at least one Spectrum object to plot'
        return

# if a list is passed, use this list
    elif (len(args) == 1 and isinstance(args[0],list)):
        splist = args[0]
    
# if a set of objects is passed, turn into a list
    else:
        splist = []
        for a in args:
            if a.__class__.__name__ == 'Spectrum':      # a spectrum object
                splist.append(a)
            elif isinstance(a,list):
                splist.append(a)
            else:
                print '\nplotSpectrum: Ignoring input object {} as it is neither a Spectrum object nor a list\n\n'.format(a)

# set up for multiplot
    if (len(splist) == 1):
        multiplot = False
    
# array of lists => force multiplot
    elif (len(splist) > 1 and isinstance(splist[0],list)):
        multiplot = True

# reformat array of spectra of multiplot is used (i.e., user forgot to set)
    if (multiplot == True and splist[0].__class__.__name__ == 'Spectrum'):
        splist = [[s] for s in splist]

    elif (multiplot == False and splist[0].__class__.__name__ == 'Spectrum'):
        splist = [splist]
        
# flatten array if multiplot is not set
    elif (multiplot == False and isinstance(splist[0],list) and len(splist) > 1):
        splist = [[item for sublist in splist for item in sublist]]       # flatten

    tot_sp = len([item for sublist in splist for item in sublist])    # Total number of spectra
    
# prep legend
    legend = kwargs.get('legend',['' for x in range(tot_sp)])
    legend = kwargs.get('legends',legend)
    legend = kwargs.get('label',legend)
    legend = kwargs.get('labels',legend)
    if(len(legend) < tot_sp):
        legend.extend(['' for x in range(tot_sp-len(legend))])
    legendLocation = kwargs.get('legendLocation','upper right')       # sets legend location
    legendLocation = kwargs.get('labelLocation',legendLocation)       # sets legend location

    
# now run a loop through the input subarrays
    plt.close('all')

# set up here for multiple file output
    if multipage == True:
        nplot = multilayout[0]*multilayout[1]
        if filetype == 'pdf':
            pdf_pages = PdfPages(filename)
        numpages = int(len(splist) / nplot) + 1
        if (len(splist) % nplot == 0):
                numpages -= 1
        fig = range(numpages)
    else:
        files = [filebase+'{}.'.format(i+1)+filetype for i in range(len(splist))]

    print multipage, splist

    pg_n = 0        # page counter
    plt_n = 0       # plot per page counter
    lg_n = 0        # legend per plot counter
    plt.close('all')
    for plts,sp in enumerate(splist):
# set specific plot parameters
        if (sp[0].__class__.__name__ != 'Spectrum'):
            raise ValueError('\nInput to plotSpectrum has wrong format:\n\n{}\n\n'.format(args[0]))
        zeropoint = kwargs.get('zeropoint',[0. for x in range(len(sp))])

# settings that work if the spectrum was read in as legitmate Spectrum object
        try:
            xlabel = kwargs.get('xlabel','{} ({})'.format(sp[0].wlabel,sp[0].wunit))
            ylabel = kwargs.get('ylabel','{} {} ({})'.format(sp[0].fscale,sp[0].flabel,sp[0].funit))
        except:
            xlabel = kwargs.get('xlabel','Wavelength (unknown units)')
            ylabel = kwargs.get('ylabel','Flux (unknown units)')
        xrange = kwargs.get('xrange',[0.85,2.42])
        bound = xrange
        ymax = [s.fluxMax().value for s in sp]
        yrng = kwargs.get('yrange',map(lambda x: x*(numpy.nanmax(ymax)+numpy.nanmax(zeropoint)),[-0.02,1.2]))
        bound.extend(yrng)
        linestyle = kwargs.get('linestyle',['steps' for x in range(len(sp))])
        linestyle = kwargs.get('linestyles',linestyle)
        if (len(linestyle) < len(sp)):
            linestyle.extend(['steps' for x in range(len(sp)-len(linestyle))])

# colors
# by default all black lines
        colors = kwargs.get('colors',['k' for x in range(len(sp))])
        colors = kwargs.get('color',colors)
        if (len(colors) < len(sp)):
            colors.extend(['k' for x in range(len(sp)-len(colors))])
        colorScheme = kwargs.get('colorScheme',None)
        colorScheme = kwargs.get('colorMap',colorScheme)
        if (colorScheme != None):
            values = range(len(sp))
            color_map = plt.get_cmap(colorScheme)
            norm  = colmap.Normalize(vmin=0, vmax=1.0*values[-1])
            scalarMap = cm.ScalarMappable(norm=norm, cmap=color_map)
            for i in range(len(sp)):
                colors[i] = scalarMap.to_rgba(values[i])
        colorsUnc = kwargs.get('colorsUnc',colors)
        colorsUnc = kwargs.get('colorUnc',colorsUnc)
        if (len(colorsUnc) < len(sp)):
            colorsUnc.extend(['k' for x in range(len(sp)-len(colorsUnc))])


# show uncertainties
        showNoise = kwargs.get('showNoise',[False for x in range(len(sp))])
        showNoise = kwargs.get('noise',showNoise)
        showNoise = kwargs.get('uncertainty',showNoise)
        if not isinstance(showNoise, list):
            showNoise = [showNoise]
        if (len(showNoise) < len(sp)):
            showNoise.extend([True for x in range(len(sp)-len(showNoise))])

# zero points - by default true
        showZero = kwargs.get('showZero',[True for x in numpy.arange(len(sp))])
        if not isinstance(showZero, list):
            showZero = [showZero]
        if (len(showZero) < len(sp)):
            showZero.extend([True for x in range(len(sp)-len(showZero))])


# GENERATE PLOTS
        if (multipage == True):
            plt_n = plts % nplot
            if (plt_n == 0):# and plts != len(splist)):
#                ax = range(nplot)
#                t = tuple([tuple([i+b*multilayout[1] for i in range(multilayout[1])]) for b in range(multilayout[0])])
#                fig[pg_n], ax = plt.subplots(multilayout[0], multilayout[1], sharex = True, sharey = True)
                fig[pg_n] = plt.figure()
                pg_n += 1
            ax = fig[pg_n-1].add_subplot(multilayout[0], multilayout[1], plt_n+1)
            
# plotting a single plot with all spectra
        else:
            plt.close('all')
#            ax = range(1)
            plt_n = 0
            if (kwargs.get('figsize') != None):
                fig = plt.figure(figsize = kwargs.get('figsize'))
            else:
                fig = plt.figure()
            ax = fig.add_subplot(111)
        
        for ii, a in enumerate(sp):
            flx = [i+zeropoint[ii] for i in a.flux.value]
#stack
            if stack > 0:
                flx = [f + (len(sp)-ii)*stack for f in flx]
                if kwargs.get('yrange') == None:
                    bound[3] = bound[3] + stack
            

            ax.plot(a.wave.value,flx,color=colors[ii],linestyle=linestyle[ii], zorder = 10, label = legend[lg_n])  

# noise
            if (showNoise[ii]):
                ns = [i+zeropoint[ii] for i in a.noise.value]
                ax.plot(a.wave.value,ns,color=colorsUnc[ii],linestyle=linestyle[ii],alpha=0.3, zorder = 10)


# zeropoint
            if (showZero[ii]):
                ze = numpy.ones(len(a.flux))*zeropoint[ii]
                ax.plot(a.wave.value,ze,color=colors[ii],linestyle=':',alpha=0.3, zorder = 10)

# determine maximum flux for all spectra
            f = interp1d(a.wave,flx,bounds_error=False,fill_value=0.)
            if (ii == 0):
                wvmax = numpy.arange(bound[0],bound[1],0.001)
                flxmax = f(wvmax)
            else:
                flxmax = numpy.maximum(flxmax,f(wvmax))

# legend counter
            lg_n = lg_n + 1 # Increment lg_n


# add comparison
        if comparison != False:
            colorComparison = kwargs.get('colorComparison',colors[0])
            linestyleComparison = kwargs.get('linestyleComparison',linestyle[0])
            ax.plot(comparison.wave.value,comparison.flux.value,color=colorComparison,linestyle=linestyleComparison,alpha=0.5, zorder = 10)

# label features
# THIS NEEDS TO BE FIXED WITH GRETEL'S STUFF
        yoff = 0.02*(bound[3]-bound[2])
        fontsize = 10-numpy.min([(multilayout[0]*multilayout[1]-1),6])
        for ftr in features:
            ftr = ftr.lower()
            if ftr in feature_labels:
                for ii,waveRng in enumerate(feature_labels[ftr]['wavelengths']):
                    if (numpy.min(waveRng) > bound[0] and numpy.max(waveRng) < bound[1]):
                        x = (numpy.arange(0,nsamples+1.0)/nsamples)* \
                            (numpy.nanmax(waveRng)-numpy.nanmin(waveRng)+0.1)+numpy.nanmin(waveRng)-0.05
                        f = interp1d(wvmax,flxmax,bounds_error=False,fill_value=0.)
                        y = numpy.nanmax(f(x))+0.5*yoff

                        if feature_labels[ftr]['type'] == 'band':
                            ax.plot(waveRng,[y+yoff]*2,color='k',linestyle='-')
                            ax.plot([waveRng[0]]*2,[y,y+yoff],color='k',linestyle='-')
                            ax.text(numpy.mean(waveRng),y+1.5*yoff,feature_labels[ftr]['label'],horizontalalignment='center',fontsize=fontsize)
                        else:
                            for w in waveRng:
                                ax.plot([w]*2,[y,y+yoff],color='k',linestyle='-')
                            ax.text(numpy.mean(waveRng),y+1.5*yoff,feature_labels[ftr]['label'],horizontalalignment='center',fontsize=fontsize)
                            waveRng = [waveRng[0]-0.05,waveRng[1]+0.05]   # for overlap

# update offset
                        foff = [y+3*yoff if (w >= waveRng[0] and w <= waveRng[1]) else 0 for w in wvmax]
                        flxmax = [numpy.max([x,y]) for x, y in zip(flxmax, foff)]

# overplot telluric absorption

        bound[3] = numpy.max(flxmax)+2.*yoff
        if (kwargs.get('telluric',False) == True):
            twv = [[1.1,1.2],[1.3,1.5],[1.75,2.0]]
            for waveRng in twv:
                rect = patches.Rectangle((waveRng[0],bound[2]),waveRng[1]-waveRng[0],bound[3]-bound[2],facecolor='grey', alpha=0.1)
                ax.add_patch(rect)
                ax.text(numpy.mean(waveRng),bound[2]+3*yoff,r'$\oplus$',horizontalalignment='center',fontsize=fontsize)


# grid
        if (grid):
            ax.grid()            
        ax.axis(bound)

# axis labels 
        fontsize = 13-numpy.min([(multilayout[0]*multilayout[1]-1),8])
        ax.set_xlabel(xlabel, fontsize = fontsize)
        ax.set_ylabel(ylabel, fontsize = fontsize)
        ax.tick_params(axis='x', labelsize=fontsize)
        ax.tick_params(axis='y', labelsize=fontsize)

# place legend
        if legendLocation == 'outside':
            box = ax.get_position()
            ax.set_position([box.x0, box.y0 + box.height * 0.15, box.width * 0.7, box.height * 0.7])
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), prop={'size':fontsize})
        else:
            ax.legend(loc=legendLocation, prop={'size':fontsize})
    
# save to file or display
        if multipage == False:
            if filebase != '':
                plt.savefig(files[plts], format=filetype)
            else:
                plt.show()
                if (kwargs.get('interactive',False) != False):
                    plt.ion()        # make window interactive 
                else:
                    plt.ioff()


# save figures in multipage format and write off pdf file
    if (multipage == True):    
        for pg_n in range(numpages):
#            fig[pg_n].text(0.5, 0.04, xlabel, ha = 'center', va = 'center')
#            fig[pg_n].text(0.06, 0.5, ylabel, ha = 'center', va = 'center', rotation = 'vertical')
            fig[pg_n].tight_layout
            fig[pg_n].suptitle(title, fontsize = 14, fontweight = 'bold')
            pdf_pages.savefig(fig[pg_n])
        if filetype == 'pdf':
            pdf_pages.close()



    return

