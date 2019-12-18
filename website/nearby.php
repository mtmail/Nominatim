<?php

require_once(CONST_BasePath.'/lib/init-website.php');
require_once(CONST_BasePath.'/lib/log.php');
require_once(CONST_BasePath.'/lib/PlaceLookup.php');
require_once(CONST_BasePath.'/lib/RadiusLookup.php');
require_once(CONST_BasePath.'/lib/output.php');
ini_set('memory_limit', '200M');

$oParams = new Nominatim\ParameterParser();

// Format for output
$sOutputFormat = $oParams->getSet('format', array('xml', 'json', 'jsonv2', 'geojson', 'geocodejson'), 'xml');
set_exception_handler_by_format($sOutputFormat);

// Preferred language
$aLangPrefOrder = $oParams->getPreferredLanguages();

$oDB = new Nominatim\DB();
$oDB->connect();

$hLog = logStart($oDB, 'nearby', $_SERVER['QUERY_STRING'], $aLangPrefOrder);

$oPlaceLookup = new Nominatim\PlaceLookup($oDB);
$oPlaceLookup->loadParamArray($oParams);
$oPlaceLookup->setIncludeAddressDetails($oParams->getBool('addressdetails', true));

$fLat = $oParams->getFloat('lat');
$fLon = $oParams->getFloat('lon');
$fRadius = $oParams->getFloat('radius', 100); // meters
$iLimit = $oParams->getInt('limit', 10);
if ($fRadius > 2000) $fRadius = 2000;


    // userError('Bulk User: Only ' . CONST_Places_Max_ID_count . ' ids are allowed in one request.');


$oRadiusLookup = new Nominatim\RadiusLookup($oDB);
$oRadiusLookup->setLimit($iLimit);

$aResults = $oRadiusLookup->lookup($fLat, $fLon, $fRadius);
if (CONST_Debug) var_dump($aResults);

if (!isset($aResults)) {
    $aResults = array();
}

// $aPlaces = $oPlaceLookup->lookup(array($oLookup->iId => $oLookup));
//     if (!empty($aPlaces)) {
//         $aPlace = reset($aPlaces);
//     }
// }

// $aSearchResults = $this->oPlaceLookup->lookup($aResults);
$aSearchResults = $oPlaceLookup->lookup($aResults);

foreach ($aSearchResults as &$r) {
    $r['name'] = $r['langaddress'];
}



logEnd($oDB, $hLog, count($aSearchResults));

if (CONST_Debug) {
    var_dump($aSearchResults);
    exit;
}

if ($sOutputFormat == 'html') {
    $sDataDate = $oDB->getOne("select TO_CHAR(lastimportdate,'YYYY/MM/DD HH24:MI')||' GMT' from import_status limit 1");
    $sTileURL = CONST_Map_Tile_URL;
    $sTileAttribution = CONST_Map_Tile_Attribution;
} elseif ($sOutputFormat == 'geocodejson') {
    // $sQuery = $fLat.','.$fLon;
    // if (isset($aPlace['place_id'])) {
    //     $fDistance = $oDB->getOne(
    //         'SELECT ST_Distance(ST_SetSRID(ST_Point(:lon,:lat),4326), centroid) FROM placex where place_id = :placeid',
    //         array(':lon' => $fLon, ':lat' => $fLat, ':placeid' => $aPlace['place_id'])
    //     );
    // }
}

if (CONST_Debug) exit;

$sOutputTemplate = ($sOutputFormat == 'jsonv2') ? 'json' : $sOutputFormat;
include(CONST_BasePath.'/lib/template/search-'.$sOutputTemplate.'.php');
