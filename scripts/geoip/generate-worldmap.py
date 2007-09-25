#!/usr/bin/python
import GeoIP
import random
import matplotlib
matplotlib.use('Agg2')
from pylab import *
from matplotlib.numerix import ma
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.toolkits.basemap import Basemap

indir='/home/jspaleta/Desktop/Fedora_World_Maps'
outdir='/home/jspaleta/Desktop/Fedora_World_Maps'
gi = GeoIP.open("/usr/share/GeoIP/GeoLiteCity.dat", GeoIP.GEOIP_MEMORY_CACHE)
random.seed()

def lookup_client_locations():
    results = []
    f = open(indir+'/ips.txt', 'r')
    for line in f:
        try:
            gir = gi.record_by_addr(line.strip())
        except:
            continue
        if gir != None:
            t = (line.strip(), gir['country_code'], gir['latitude'], gir['longitude'])
            results.append(t)
    f.close()
    return results


def lookup_host_locations():
    results = []
    for h in Host.select():
        if h.private or h.site.private or \
               not h.user_active or not h.admin_active or \
               not h.site.user_active or not h.site.admin_active:
            continue
        try:
            gir = gi.record_by_name(h.name)
        except:
            print "Cannot find location for %s" % (h.name)
            continue
        if gir != None:
            t = (h.name, gir['country_code'], gir['latitude'], gir['longitude'])
            results.append(t)

    return results

def draw_client_density():

    m = Basemap(llcrnrlon=-180.,llcrnrlat=-90,urcrnrlon=180.,urcrnrlat=90.,\
                resolution='c',projection='cyl')

    # plot them as filled circles on the map.
    # first, create a figure.
    dpi=100
    dimx=800/dpi
    dimy=400/dpi
    fig=figure(figsize=(dimx,dimy), dpi=dpi, frameon=False, facecolor='blue')
#    ax=fig.add_axes([0.1,0.1,0.7,0.7],axisbg='g')
    ax=fig.add_axes([0.0,0.0,1.0,1.0],axisbg='g')
    canvas = FigureCanvas(fig)
    results = lookup_client_locations()
    X,Y,Z = find_client_density(m,results)
#    s = random.sample(results, 40000)
#    for t in s:
#        lat=t[2]
#        lon=t[3]
#        # draw a red dot at the center.
#        xpt, ypt = m(lon, lat)
#        m.plot([xpt],[ypt],'ro', zorder=10)
    # draw coasts and fill continents.
    m.drawcoastlines(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    m.drawlsmask([100,100,100,0],[0,0,255,255])
#    m.fillcontinents(color='green')
    palette = cm.YlOrRd
    m.imshow(Z,palette,extent=(m.xmin,m.xmax,m.ymin,m.ymax),interpolation='gaussian',zorder=0)
#    l,b,w,h = ax.get_position()
#    cax = axes([l+w+0.075, b, 0.05, h])
#    colorbar(cax=cax) # draw colorbar

    canvas.print_figure(outdir+'/clientmap.png', dpi=100)


def find_client_density(m,client_locations,latscale=1.0,lonscale=1.0,lat_smooth=1,lon_smooth=1):
    lat_array=arange(m.ymin,m.ymax+latscale,latscale)
    lon_array=arange(m.xmin,m.xmax+lonscale,lonscale)
    maxlat=len(lat_array)-1
    maxlon=len(lon_array)-1
    Z=zeros((len(lat_array),len(lon_array)),dtype='float')
    for client in client_locations:
      lat=client[2]
      i_lat=int(float((lat-lat_array[0]))/float(latscale)) 
      lon=client[3]
      i_lon=int(float((lon-lon_array[0]))/float(lonscale)) 
      for i in xrange(-int(lat_smooth),int(lat_smooth+1),1):
        for j in xrange(-int(lon_smooth),int(lon_smooth+1),1):
          if ( i_lat+i >= 0 ) and (i_lat+i < maxlat) : 
            if ( i_lon+j >= 0) and ( i_lon+j < maxlon) :
              Z[i_lat+i,i_lon+j]+=1.0
    Lon,Lat=meshgrid(lon_array,lat_array)
    X,Y=m(Lon,Lat)
    Z= Z + 1.0
    Z=log(Z)
    Z = where(Z <= 0.,1.e10,Z)
    Z = ma.masked_values(Z, 1.e10)
    return X,Y,Z
    
def main():
    draw_client_density()



if __name__ == "__main__":
    sys.exit(main())
        
