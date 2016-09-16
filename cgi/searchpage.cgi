#!/usr/bin/perl

use strict;
use utf8;
use CGI;
use CGI::Cookie;
use DBI;
use lib ('/home/takahashi/perl/local/lib/perl5');
use HTML::Template;
use HTML::Entities;
use Encode;
use Data::Dumper;
use DateTime;
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';
require 'timeline.pl';

sub searchpage_operator {
	# Config
	my $SEARCH_PAGE_TMPL_PATH = '../tmpl/searchpage.tmpl';
	my $MAIN_PAGE_CGI_PATH = '../cgi/mainpage.cgi';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name = decode_utf8($CGI->cookie('user_name'));
	my $user_password = decode_utf8($CGI->cookie('user_password'));
	my $search_text_by_cookie = decode_utf8($CGI->cookie('search_text'));

	# Get param
	my $search_text = decode_utf8($CGI->param('text'));

	# Set head
	my $status_code = '';
	my $mode;
	if((!(defined $CGI->param('text')) && !(defined $CGI->cookie('search_text')))){
		$status_code = '302';
		$mode = 'jumpMainPage';
	}elsif(($CGI->param('text') eq '') || ($CGI->cookie('search_text') eq '')){
		$status_code = '302';
		$mode = 'jumpMainPageWithError';
	}else{
		$status_code = '200';
		$mode = 'showPage';
	}
	my @HEADER = (
			-type => 'text/html',
			-charset => "utf-8",
			-status => $status_code
		);

	# Body
	if($mode eq 'showPage'){

		# Cookie Text
		if(!(defined $CGI->param('text'))){
			$search_text = $search_text_by_cookie;
		}

		# Check account
		my $is_login = 0;
		my $user_id = -1;
		if(defined $CGI->cookie('user_name') && defined $CGI->cookie('user_password')){
			if(($user_id = Utils::checkAccount($user_name, $user_password)) == -1){
				push @HEADER , ('-status', '400');
				print $CGI->header(@HEADER);
				return;
			}
			$is_login = 1;
		}

		# Load tmpl
		my $this_page_tmpl = HTML::Template->new(
			filename => $SEARCH_PAGE_TMPL_PATH,
			utf8 => 1
		);

		# Make TimeLine
		my $encoded_search_text = '%'.Utils::encodeHTMLMulti($search_text).'%';
		my $timeline_tmpl = makeTimeLine($CGI, 'WHERE tweet.text LIKE ?', [$encoded_search_text], ($is_login == 1)? $user_id : '', '');
		$this_page_tmpl->param('TIMELINE_TMPL' => $timeline_tmpl->output);

		# Add cookie
		my $cookie_search_text = new CGI::Cookie(-name=>'search_text',-value=>$search_text);
		push @HEADER , ('-cookie',[$cookie_search_text]);

		# Attach Search Text
		$this_page_tmpl->param(SEARCH_RESULT_AREA => '「'.HTML::Entities::encode_entities($search_text).'」の検索結果');
		$this_page_tmpl->param(SEARCH_TEXT_INPUT_TAG => '<input type="text" name="text" class="form-control" placeholder="Twitterを検索" value="'.HTML::Entities::encode_entities($search_text).'">');

		# Set Header
		print $CGI->header(@HEADER), $this_page_tmpl->output;

	}elsif($mode eq 'jumpMainPage'){

		# Add location
		push @HEADER , ('-location',$MAIN_PAGE_CGI_PATH);

		print $CGI->header(@HEADER);
	}elsif($mode eq 'jumpMainPageWithError'){
		# Add location
		push @HEADER , ('-location',$MAIN_PAGE_CGI_PATH.'?&search_empty=1');

		print $CGI->header(@HEADER);
	}

}

searchpage_operator();
