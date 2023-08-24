#!/usr/bin/python3

from osgeo import ogr, osr
import os
import glob
import math

driver = ogr.GetDriverByName('GeoJSON')
# viridis colors from https://observablehq.com/@d3/color-schemes
colors = [
    {
        "range": [2784.4, 100000.0],
        "color": "#440154"
    },
    {
        "range": [807.3, 2784.4],
        "color": "#482878"
    },
    {
        "range": [538.2, 807.3],
        "color": "#3e4989"
    },
    {
        "range": [198.5, 538.2],
        "color": "#31688e"
    },
    {
        "range": [116.8, 198.5],
        "color": "#26828e"
    },
    {
        "range": [87.2, 116.8],
        "color": "#1f9e89"
    },
    {
        "range": [51.9, 87.2],
        "color": "#35b779"
    },
    {
        "range": [23.1, 51.9],
        "color": "#6ece58"
    },
    {
        "range": [5.1, 23.1],
        "color": "#b5de2b"
    },
    {
        "range": [0, 5.1],
        "color": "#fde725"
    }
]

def transform(filePath):
    fileName = os.path.basename(filePath)
    baseName = fileName.replace(".geojson", "").replace("_pt", "")

    print(f"Transforming {fileName}")

    # get the input layer
    inDataSet = driver.Open(filePath)
    inLayer = inDataSet.GetLayer()

    inSpatialRef = inLayer.GetSpatialRef()

    # loading projection
    sr = osr.SpatialReference(str(inSpatialRef))

    # detecting EPSG/SRID
    res = sr.AutoIdentifyEPSG()

    srid = sr.GetAuthorityCode(None)

    # input SpatialReference
    inSpatialRef.ImportFromEPSG(int(srid))

    # output SpatialReference
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(4326)
    outSpatialRef.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    # create the CoordinateTransformation
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

    # create the output layer
    outputShapefile = f"./output/{baseName}.geojson"

    if os.path.exists(outputShapefile):
        driver.DeleteDataSource(outputShapefile)

    outDataSet = driver.CreateDataSource(outputShapefile)
    outLayer = outDataSet.CreateLayer(baseName, geom_type=ogr.wkbPoint)

    # add fields
    inLayerDefn = inLayer.GetLayerDefn()

    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)

    # new field
    radiusField = ogr.FieldDefn("radius", ogr.OFTReal)
    outLayer.CreateField(radiusField)
    colorField = ogr.FieldDefn("color", ogr.OFTString)
    outLayer.CreateField(colorField)

    # get the output layer's feature definition
    outLayerDefn = outLayer.GetLayerDefn()

    # loop through the input features
    inFeature = inLayer.GetNextFeature()

    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(coordTrans)
        # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry
        outFeature.SetGeometry(geom)
        # calculate radius from the L_area
        radius = None
        color = "#000000"
        for i in range(0, outLayerDefn.GetFieldCount()):
            fieldName = outLayerDefn.GetFieldDefn(i).GetNameRef()
            if fieldName == "L_area":
                fieldValue = inFeature.GetField(i)
                radius = math.sqrt(fieldValue/3.14159)
            elif fieldName == "VOC_g_y":
                fieldValue = inFeature.GetField(i)
                scheme = [d for d in colors if d["range"][0] <= fieldValue and fieldValue < d["range"][1]]
                color = scheme[0]["color"]
        # set the attributes
        for i in range(0, outLayerDefn.GetFieldCount()):
            fieldName = outLayerDefn.GetFieldDefn(i).GetNameRef()
            fieldValue = radius if fieldName == "radius" else (color if fieldName == "color" else inFeature.GetField(i))
            outFeature.SetField(fieldName, fieldValue)
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # destroy the features and get the next input feature
        outFeature.Destroy()
        inFeature.Destroy()
        inFeature = inLayer.GetNextFeature()

    # close the shapefiles
    inDataSet.Destroy()
    outDataSet.Destroy()

# main
for file in glob.glob("./input/*_pt.geojson"):
    transform(file)